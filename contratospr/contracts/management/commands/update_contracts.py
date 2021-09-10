from django.core.management.base import BaseCommand

from ...models import Contract
from ...tasks import scrape_contracts


class Command(BaseCommand):
    help = "Update local contracts with data from remote source"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=None)
        parser.add_argument("--offset", nargs="?", type=int, default=None)

    def handle(self, *args, **options):
        limit = options.pop("limit", 1000)
        offset = options.pop("offset", 0)
        contracts = (
            Contract.objects.select_related("entity")
            .all()
            .order_by("-date_of_grant")
            .only("pk", "number", "entity")[offset : offset + limit]
        )

        for contract in contracts.iterator():
            self.stdout.write(f"=> Scraping contract {contract.pk} / {contract.number}")
            scrape_contracts.delay(
                contract_number=contract.number, entity_id=contract.entity.source_id
            )
