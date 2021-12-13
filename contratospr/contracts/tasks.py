import re
from datetime import date, datetime

import pytz
from celery import chain
from dateutil.relativedelta import relativedelta
from structlog import get_logger

from ..tasks import app
from .models import (
    CollectionJob,
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from .scraper import (
    BASE_CONTRACT_URL,
    get_amendments,
    get_contractors,
    get_contracts,
    send_document_request,
)
from .search import index_contract

logger = get_logger(__name__)


def parse_date(value):
    if not value:
        return None

    ms = int(re.search(r"\d+", value).group())
    return datetime.utcfromtimestamp(ms // 1000).replace(tzinfo=pytz.UTC)


def strip_whitespace(value):
    return value.strip() if value else None


def normalize_contract(contract):
    result = {
        "entity_id": contract["EntityId"],
        "entity_name": strip_whitespace(contract["EntityName"]),
        "contract_id": contract["ContractId"],
        "contract_number": contract["ContractNumber"],
        "amendment": contract["Amendment"],
        "date_of_grant": parse_date(contract["DateOfGrant"]),
        "effective_date_from": parse_date(contract["EffectiveDateFrom"]),
        "effective_date_to": parse_date(contract["EffectiveDateTo"]),
        "service": strip_whitespace(contract["Service"]),
        "service_group": strip_whitespace(contract["ServiceGroup"]),
        "cancellation_date": parse_date(contract["CancellationDate"]),
        "amount_to_pay": contract["AmountToPay"],
        "has_amendments": contract["HasAmendments"],
        "document_id": contract["DocumentWithoutSocialSecurityId"],
        "exempt_id": contract["ExemptId"],
        "contractors": [],
        "amendments": [],
    }

    if result["document_id"]:
        document_id = result["document_id"]
        result[
            "document_url"
        ] = f"{BASE_CONTRACT_URL}/downloaddocument?code={document_id}"

    return result


def normalize_contractors(contractors):
    results = []

    for contractor in contractors:
        results.append(
            {
                "contractor_id": contractor["ContractorId"],
                "entity_id": contractor["EntityId"],
                "name": contractor["Name"]
                or contractor["ConfirmedName1"]
                or contractor["ConfirmedName2"],
            }
        )

    return results


@app.task
def expand_contract(contract):
    logger.info("Expanding contract", contract=contract["ContractNumber"])

    result = normalize_contract(contract)

    contractors = get_contractors(result["contract_id"])

    result["contractors"] = normalize_contractors(contractors)

    if result["has_amendments"]:
        amendments = get_amendments(result["contract_number"], result["entity_id"])

        for amendment in amendments:
            result["amendments"].append(expand_contract(amendment))

    return result


@app.task
def download_document(document_id):
    document = Document.objects.get(pk=document_id)

    # Download document and upload to S3
    document.download()

    return document


@app.task
def detect_text(document_id):
    logger.info("Detecting document text", document_id=document_id)
    document = Document.objects.get(pk=document_id)

    document.detect_text()

    for contract in document.contract_set.all():
        logger.info(
            "Indexing document contracts",
            document_id=document_id,
            contract_id=contract.pk,
        )
        index_contract(contract)

    return document


@app.task
def request_contract_document(contract_id):
    return send_document_request(contract_id)


@app.task
def update_contract(result, parent_id=None, skip_doc_tasks=False):
    logger.info(
        "Updating contract", contract=result["contract_number"], parent_id=parent_id
    )

    artifacts = []

    entity, entity_created = Entity.objects.get_or_create(
        source_id=result["entity_id"], defaults={"name": result["entity_name"]}
    )
    artifacts.append({"obj": entity, "created": entity_created})

    service_group, service_group_created = ServiceGroup.objects.get_or_create(
        name=result["service_group"]
    )
    artifacts.append({"obj": service_group, "created": service_group_created})

    service, service_created = Service.objects.get_or_create(
        name=result["service"], group=service_group
    )
    artifacts.append({"obj": service, "created": service_created})

    contract_data = {
        "entity": entity,
        "number": result["contract_number"],
        "amendment": result["amendment"],
        "date_of_grant": result["date_of_grant"],
        "effective_date_from": result["effective_date_from"],
        "effective_date_to": result["effective_date_to"],
        "service": service,
        "cancellation_date": result["cancellation_date"],
        "amount_to_pay": result["amount_to_pay"],
        "has_amendments": result["has_amendments"],
        "exempt_id": result["exempt_id"],
        "parent_id": parent_id,
    }

    if result["document_id"]:
        document, document_created = Document.objects.update_or_create(
            source_id=result["document_id"],
            defaults={"source_url": result["document_url"]},
        )

        if document_created and skip_doc_tasks:
            chain(download_document.si(document.pk), detect_text.si(document.pk))()

        artifacts.append({"obj": document, "created": document_created})

        contract_data["document"] = document

    contract, contract_created = Contract.objects.update_or_create(
        source_id=result["contract_id"], defaults=contract_data
    )
    artifacts.append({"obj": contract, "created": contract_created})

    for contractor_result in result["contractors"]:
        contractor, contractor_created = Contractor.objects.get_or_create(
            source_id=contractor_result["contractor_id"] or contract.source_id,
            defaults={
                "name": contractor_result["name"],
                "entity_id": contractor_result["entity_id"],
            },
        )

        artifacts.append({"obj": contractor, "created": contractor_created})

        contract.contractors.add(contractor)

    for amendment_result in result["amendments"]:
        amendment_artifacts = update_contract(
            amendment_result, parent_id=contract.pk, skip_doc_tasks=skip_doc_tasks
        )
        artifacts.extend(amendment_artifacts)

    if not skip_doc_tasks:
        index_contract(contract)

    return artifacts


@app.task
def scrape_contracts(limit=None, max_items=None, **kwargs):
    offset = 0
    total_records = 0
    default_limit = 10
    real_limit = limit or default_limit
    skip_doc_tasks = kwargs.pop("skip_doc_tasks", False)
    collection_job_id = kwargs.pop("collection_job_id", None)
    collection_job = None
    if collection_job_id:
        collection_job = CollectionJob.objects.get(pk=collection_job_id)

    while offset <= total_records:
        logger.info(
            "Scraping contracts",
            limit=limit,
            real_limit=real_limit,
            offset=offset,
            total_records=total_records,
        )

        contracts = get_contracts(offset, real_limit, **kwargs)

        if not total_records:
            total_records = max_items if max_items else contracts["recordsFiltered"]

        for contract in contracts["data"]:
            expanded = expand_contract(contract)
            results = update_contract(expanded, skip_doc_tasks=skip_doc_tasks)

            if collection_job:
                collection_job.create_artifacts(results)

        offset += real_limit


@app.task
def collect_data(date_of_grant_start=None, date_of_grant_end=None):
    now = datetime.utcnow()

    if isinstance(date_of_grant_start, str):
        date_of_grant_start = date.fromisoformat(date_of_grant_start)
    else:
        date_of_grant_start = now + relativedelta(
            months=-1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

    if isinstance(date_of_grant_end, str):
        date_of_grant_end = date.fromisoformat(date_of_grant_end)
    else:
        date_of_grant_end = (
            now
            + relativedelta(months=-1, day=1, hour=0, minute=0, second=0, microsecond=0)
            + relativedelta(months=+1, days=-1)
        )

    job = CollectionJob.objects.create(
        date_of_grant_start=date_of_grant_start, date_of_grant_end=date_of_grant_end
    )
    job.process()
