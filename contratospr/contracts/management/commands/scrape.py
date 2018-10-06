import asyncio
import random
import re
from datetime import datetime

import aiohttp
import pytz
from django.core.management.base import BaseCommand

from ...models import Contract, Contractor, Document, Entity, Service

BASE_URL = "https://consultacontratos.ocpr.gov.pr"
BASE_CONTRACT_URL = f"{BASE_URL}/contract"
BASE_CONTRACTOR_URL = f"{BASE_URL}/contractor"


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0",
]


def parse_date(value):
    if not value:
        return None

    ms = int(re.search("\d+", value).group())
    return datetime.utcfromtimestamp(ms // 1000).replace(tzinfo=pytz.UTC)


def strip_whitespace(value):
    return value.strip() if value else None


async def expand_contract(session, contract):
    result = {
        "entity_id": contract["EntityId"],
        "entity_name": strip_whitespace(contract["EntityName"]),
        "contract_id": contract["ContractId"],
        "contract_number": contract["ContractNumber"],
        "amendment": contract["Amendment"],
        "date_of_grant": parse_date(contract["DateOfGrant"]),
        "effective_date_from": parse_date(contract["EffectiveDateFrom"]),
        "effective_date_to": parse_date(contract["EffectiveDateTo"]),
        "service": contract["Service"],
        "service_group": contract["ServiceGroup"],
        "cancellation_date": parse_date(contract["CancellationDate"]),
        "amount_to_pay": contract["AmountToPay"],
        "has_amendments": contract["HasAmendments"],
        "document_id": contract["DocumentWithoutSocialSecurityId"],
        "exempt_id": contract["ExemptId"],
        "contractors": contract["Contractors"],
        "amendments": [],
    }

    if result["document_id"]:
        document_id = result["document_id"]
        result[
            "document_url"
        ] = f"{BASE_CONTRACT_URL}/downloaddocument?documentid={document_id}"

    result["contractors"] = await get_contractors(session, result["contract_id"])

    if result["has_amendments"]:
        result["amendments"] = await get_amendments(
            session, result["contract_number"], result["entity_id"]
        )

    return result


async def get_contractors(session, contract_id):
    contractors = []

    async with session.post(
        f"{BASE_CONTRACTOR_URL}/findbycontractid",
        json={"contractId": contract_id},
        headers={"user-agent": random.choice(USER_AGENTS)},
    ) as response:
        response_json = await response.json()

        for contractor in response_json:
            contractors.append(
                {
                    "contractor_id": contractor["ContractorId"],
                    "entity_id": contractor["EntityId"],
                    "name": contractor["Name"],
                }
            )

    return contractors


async def get_amendments(session, contract_number, entity_id):
    results = []

    async with session.post(
        f"{BASE_CONTRACT_URL}/getamendments",
        json={"contractNumber": contract_number, "entityId": entity_id},
        headers={"user-agent": random.choice(USER_AGENTS)},
    ) as response:
        amendments = await response.json()

        for amendment in amendments:
            results.append(await expand_contract(session, amendment))

    return results


async def search(session, offset=0, limit=10):
    async with session.post(
        f"{BASE_CONTRACT_URL}/search",
        json={
            "start": offset,
            "length": limit,
            "order": [{"column": 3, "dir": "desc"}],
        },
        headers={"user-agent": random.choice(USER_AGENTS)},
    ) as response:
        tasks = []
        response_json = await response.json()

        for result in response_json["data"]:
            tasks.append(expand_contract(session, result))

        return tasks


def update_contract(result, parent=None):
    entity, _ = Entity.objects.get_or_create(
        source_id=result["entity_id"], defaults={"name": result["entity_name"]}
    )

    service, _ = Service.objects.get_or_create(
        name=result["service"], group=result["service_group"]
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
        "parent": parent,
    }

    if result["document_id"]:
        document, _ = Document.objects.get_or_create(
            source_id=result["document_id"],
            defaults={"source_url": result["document_url"]},
        )

        contract_data["document"] = document

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
        update_contract(amendment_result, contract)

    return contract


class Command(BaseCommand):
    help = "Scrape search results"

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._scrape())

    async def _scrape(self):
        async with aiohttp.ClientSession() as session:
            offset = 0
            limit = 1000
            total_records = 887865
            tasks = []

            while offset < total_records:
                self.stdout.write(f"==> {offset} / {total_records}")
                search_tasks = await search(session, offset=offset, limit=limit)
                tasks.extend(search_tasks)
                offset += limit

            results = await asyncio.gather(*tasks)

            for result in results:
                contract = update_contract(result, parent=None)
                self.stdout.write(f"=> {contract}")
