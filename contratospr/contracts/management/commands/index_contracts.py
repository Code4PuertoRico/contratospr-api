from django.core.management.base import BaseCommand

from ...models import Contract
from ...search import index_contract


class Command(BaseCommand):
    help = "Index contracts"

    def handle(self, *args, **options):
        contracts = Contract.objects.all().iterator()

        for contract in contracts:
            index_contract(contract)
