from django.core.management.base import BaseCommand

from ...models import Contract
from ...search import search_vector


class Command(BaseCommand):
    help = "Index contracts"

    def handle(self, *args, **options):
        contracts = (
            Contract.objects.select_related("document")
            .prefetch_related("contractors")
            .annotate(search=search_vector)
            .all()
        )

        for contract in contracts:
            contract.search_vector = contract.search
            contract.save(update_fields=["search_vector"])
            self.stdout.write(f"Indexed contract {contract.id}")
