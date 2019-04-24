import json

from django.core.management.base import BaseCommand
from structlog import get_logger

from ...scraper import get_amendments, get_contractors, get_contracts, get_entities

logger = get_logger("contratospr.commands.download_contracts")


def get_contracts_by_entity(entity):
    offset = 0
    total_records = 0
    limit = 1000

    entity_id = entity["Code"]
    entity_name = entity["Name"].strip()

    while offset <= total_records:
        logger.info(
            "Scraping contracts",
            limit=limit,
            entity_id=entity_id,
            entity_name=entity_name,
            offset=offset,
            total_records=total_records,
        )

        contracts_json = get_contracts(offset, limit, entity_id=entity_id)

        with open(f"data/contracts-{entity_id}-{offset}.json", "w+") as f:
            json.dump(contracts_json, f)

        expanded_contracts = []

        for contract_data in contracts_json.get("data", []):
            try:
                logger.info(
                    "Getting contractors", contract_id=contract_data["ContractId"]
                )
                contract_data["_Contractors"] = get_contractors(
                    contract_data["ContractId"]
                )
                contract_data["_Amendments"] = None

                if contract_data["HasAmendments"]:
                    logger.info(
                        "Getting amendments",
                        contract_number=contract_data["ContractNumber"],
                        entity_id=contract_data["EntityId"],
                    )
                    contract_data["_Amendments"] = get_amendments(
                        contract_data["ContractNumber"], contract_data["EntityId"]
                    )
            except Exception as exc:
                logger.info(
                    "Error extending contract",
                    contract_id=contract_data["ContractId"],
                    exception=exc,
                )

            expanded_contracts.append(contract_data)

        contracts_json["data"] = expanded_contracts

        with open(f"data/contracts-{entity_id}-{offset}.json", "w+") as f:
            json.dump(contracts_json, f)

        if not total_records:
            total_records = contracts_json["recordsFiltered"]

        offset += limit


def get_contracts_by_entities(entities):
    for entity in entities:
        get_contracts_by_entity(entity)


class Command(BaseCommand):
    help = "Download contracts for entities from consultacontratos.ocpr.gov.pr"

    def add_arguments(self, parser):
        parser.add_argument("--file", nargs="?", type=str, default=None)

    def handle(self, *args, **options):
        entities_file_path = options.get("file")

        if entities_file_path:
            entities = json.load(open(entities_file_path)).get("Results", [])
        else:
            entities = get_entities()

        get_contracts_by_entities(entities)
