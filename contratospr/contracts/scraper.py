import random

import requests

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


def get_contractors(contract_id):
    response = requests.post(
        f"{BASE_CONTRACTOR_URL}/findbycontractid",
        json={"contractId": contract_id},
        headers={"user-agent": random.choice(USER_AGENTS)},
    )

    return response.json()


def get_amendments(contract_number, entity_id):
    response = requests.post(
        f"{BASE_CONTRACT_URL}/getamendments",
        json={"contractNumber": contract_number, "entityId": entity_id},
        headers={"user-agent": random.choice(USER_AGENTS)},
    )

    return response.json()


def get_contracts(offset, limit):
    response = requests.post(
        f"{BASE_CONTRACT_URL}/search",
        json={
            "start": offset,
            "length": limit,
            "order": [{"column": 3, "dir": "desc"}],
        },
        headers={"user-agent": random.choice(USER_AGENTS)},
    )

    return response.json()
