import gzip
import json
import os

from django.core.management.base import BaseCommand
from structlog import get_logger

from ...tasks import normalize_contract, normalize_contractors, update_contract

logger = get_logger("contratospr.commands.import_contracts")


def _normalize_contract(contract):
    normalized_contract = normalize_contract(contract)
    normalized_contract["contractors"] = normalize_contractors(
        contract.get("_Contractors", [])
    )

    if contract.get("_Amendments"):
        for amendment in contract.get("_Amendments", []):
            normalized_contract["amendments"].append(_normalize_contract(amendment))

    return normalized_contract


def import_contracts(contracts):
    for contract in contracts:
        normalized = _normalize_contract(contract)

        logger.info(
            "Importing contract",
            contract_id=normalized["contract_id"],
            entity_id=normalized["entity_id"],
        )

        update_contract(normalized)


class Command(BaseCommand):
    help = "Import contracts"

    def handle(self, *args, **options):
        gzipped_merged_file_name = "contracts.jsonl.gz"
        gzipped_merged_file_path = os.path.join("data", gzipped_merged_file_name)

        with gzip.open(gzipped_merged_file_path, "r") as f:
            for jsonline in f:
                contracts_data = json.loads(jsonline)
                import_contracts(contracts_data)
