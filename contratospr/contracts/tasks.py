import datetime
import re

import dramatiq
import pytz
from django.conf import settings
from dramatiq.rate_limits import ConcurrentRateLimiter
from dramatiq.rate_limits.backends import RedisBackend

from .models import Contract, Contractor, Document, Entity, Service, ServiceGroup
from .scraper import (
    BASE_CONTRACT_URL,
    get_amendments,
    get_contractors,
    get_contracts,
    send_document_request,
)
from .search import index_contract

backend = RedisBackend(url=settings.REDIS_URL)
DISTRIBUTED_MUTEX = ConcurrentRateLimiter(backend, "distributed-mutex", limit=1)


def parse_date(value):
    if not value:
        return None

    ms = int(re.search(r"\d+", value).group())
    return datetime.datetime.utcfromtimestamp(ms // 1000).replace(tzinfo=pytz.UTC)


def strip_whitespace(value):
    return value.strip() if value else None


@dramatiq.actor
def expand_contract(contract):
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
        ] = f"{BASE_CONTRACT_URL}/downloaddocument?documentid={document_id}"

    contractors = get_contractors(result["contract_id"])

    for contractor in contractors:
        result["contractors"].append(
            {
                "contractor_id": contractor["ContractorId"],
                "entity_id": contractor["EntityId"],
                "name": contractor["Name"],
            }
        )

    if result["has_amendments"]:
        amendments = get_amendments(result["contract_number"], result["entity_id"])

        for amendment in amendments:
            result["amendments"].append(expand_contract(amendment))

    return result


@dramatiq.actor
def download_document(document_id):
    with DISTRIBUTED_MUTEX.acquire():
        document = Document.objects.get(pk=document_id)

        # Download document and upload to S3
        document.download()


@dramatiq.actor
def generate_preview(document_id):
    with DISTRIBUTED_MUTEX.acquire():
        document = Document.objects.get(pk=document_id)

        # Try to generate preview with FilePreviews
        document.generate_preview()


@dramatiq.actor
def detect_text(document_id, force=False):
    # Use Cloud Vision API if no text was extracted with FilePreviews
    document = Document.objects.get(pk=document_id)

    if document.preview_data:
        extracted_text = []

        original_file = document.preview_data["original_file"] or {
            "metadata": {"ocr": []}
        }

        for ocr_result in original_file["metadata"]["ocr"]:
            extracted_text.append(ocr_result["text"].strip())

        if force or len("".join(extracted_text)) < 100:
            document.detect_text()

            for contract in document.contract_set.all():
                index_contract(contract)


@dramatiq.actor
def request_contract_document(contract_id):
    return send_document_request(contract_id)


@dramatiq.actor
def update_contract(result, parent_id=None):
    entity, _ = Entity.objects.get_or_create(
        source_id=result["entity_id"], defaults={"name": result["entity_name"]}
    )

    service_group, _ = ServiceGroup.objects.get_or_create(name=result["service_group"])

    service, _ = Service.objects.get_or_create(
        name=result["service"], group=service_group
    )

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
        document, created = Document.objects.update_or_create(
            source_id=result["document_id"],
            defaults={"source_url": result["document_url"]},
        )

        contract_data["document"] = document

        if created:
            download_document.send(document.pk)

    contract, _ = Contract.objects.update_or_create(
        source_id=result["contract_id"], defaults=contract_data
    )

    for contractor_result in result["contractors"]:
        contractor, _ = Contractor.objects.get_or_create(
            source_id=contractor_result["contractor_id"],
            defaults={
                "name": contractor_result["name"],
                "entity_id": contractor_result["entity_id"],
            },
        )

        contract.contractors.add(contractor)

    for amendment_result in result["amendments"]:
        update_contract.send(amendment_result, parent_id=contract.pk)

    index_contract(contract)

    return contract.pk


@dramatiq.actor
def scrape_contracts(limit=None, effective_start=None, effective_end=None):
    offset = 0
    total_records = 0
    default_limit = 1000

    while offset <= total_records:
        real_limit = limit or default_limit
        contracts = get_contracts(
            offset,
            real_limit,
            effective_start=effective_start,
            effective_end=effective_end,
        )

        if not total_records:
            total_records = limit if limit else contracts["recordsFiltered"]

        for contract in contracts["data"]:
            dramatiq.pipeline(
                [expand_contract.message(contract), update_contract.message()]
            ).run()

        offset += real_limit
