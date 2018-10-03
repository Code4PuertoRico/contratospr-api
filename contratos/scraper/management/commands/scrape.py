import asyncio
import random
import re
from datetime import datetime

from django.core.management.base import BaseCommand

import aiohttp

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
    ms = int(re.search("\d+", value).group())
    return datetime.utcfromtimestamp(ms // 1000)


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
        "cancellation_date": contract["CancellationDate"],
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
    async with session.post(
        f"{BASE_CONTRACTOR_URL}/findbycontractid",
        json={"contractId": contract_id},
        headers={"user-agent": random.choice(USER_AGENTS)},
    ) as response:
        return await response.json()


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


async def search(session, start=0, length=10):
    tasks = []

    async with session.post(
        f"{BASE_CONTRACT_URL}/search",
        json={
            "start": start,
            "length": length,
            "order": [{"column": 3, "dir": "desc"}],
        },
        headers={"user-agent": random.choice(USER_AGENTS)},
    ) as response:
        response_json = await response.json()

        for result in response_json["data"]:
            task = asyncio.create_task(expand_contract(session, result))
            tasks.append(task)

    return tasks


async def scrape():
    async with aiohttp.ClientSession() as session:
        tasks = []
        start = 0

        while start < 100:
            search_tasks = await search(session, start=start, length=10)

            if not search_tasks:
                break

            tasks.extend(search_tasks)
            start += 10

        return await asyncio.gather(*tasks)


class Command(BaseCommand):
    help = "Scrape search results"

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(scrape())
        print(results)
