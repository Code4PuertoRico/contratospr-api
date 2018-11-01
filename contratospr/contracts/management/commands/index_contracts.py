from django.core.management.base import BaseCommand

from ...models import Contract
from ...search import index_contract


class Command(BaseCommand):
    help = "Index contracts"

    def handle(self, *args, **options):
        contracts = (
            Contract.objects.select_related("document", "entity")
            .prefetch_related("contractors")
            .defer("document__preview_data", "document__vision_data")
            .all()
        )

        for contract in contracts:
            index_contract(contract)
            self.stdout.write(f"Indexed contract {contract.id}")
