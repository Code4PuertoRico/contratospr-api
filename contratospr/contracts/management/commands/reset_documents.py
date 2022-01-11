from django.core.management.base import BaseCommand

from ...models import Document
from ...search import index_contract


class Command(BaseCommand):
    help = "Delete all documents in S3, clears extracted pages, and reindex contracts."

    def handle(self, *args, **options):
        documents = Document.objects.exclude(file="").defer("pages")

        for document in documents:
            self.stdout.write(f"=> Resetting document {document.pk}")

            self.stdout.write("==> Deleting file")
            document.file.delete()

            self.stdout.write("==> Clearing pages")
            document.pages = None
            document.save(update_fields=["pages"])

            self.stdout.write("==> Indexing contracts")
            for contract in document.contract_set.all():
                self.stdout.write(f"===> Indexing contract {contract.pk}")
                index_contract(contract)
