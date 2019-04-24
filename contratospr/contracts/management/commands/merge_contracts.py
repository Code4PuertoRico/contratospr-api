import gzip
import json
import os
import shutil

from django.core.management.base import BaseCommand
from structlog import get_logger

logger = get_logger("contratospr.commands.merge_contracts")


class Command(BaseCommand):
    help = "Merge contracts"

    def handle(self, *args, **options):
        merged_file_name = "contracts.json"
        merged_file_path = os.path.join("data", merged_file_name)
        gzipped_merged_file_name = "contracts.jsonl.gz"
        gzipped_merged_file_path = os.path.join("data", gzipped_merged_file_name)

        for filename in os.listdir("data"):
            file_path = os.path.join("data", filename)

            if (
                os.path.isfile(file_path)
                and file_path.endswith(".json")
                and file_path != merged_file_name
                and file_path != gzipped_merged_file_name
            ):
                logger.info("Merging contracts", filename=filename)

                with open(file_path) as f:
                    contracts_json = json.load(f)

                contracts_data = contracts_json.get("data", [])

                json_str = f"{json.dumps(contracts_data)}\n"

                with open(merged_file_path, "a+") as f:
                    f.write(json_str)

        with open(merged_file_path, "rb") as f_in:
            with gzip.open(gzipped_merged_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
