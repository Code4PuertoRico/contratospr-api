from django.core.management.base import BaseCommand

from ...models import Document
from ...tasks import download_document


class Command(BaseCommand):
    help = "Download the next N contract documents"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=1000)

    def handle(self, *args, **options):
        limit = options.get("limit")
        documents = Document.objects.filter(file="").only("pk")[:limit]

        for document in documents:
            self.stdout.write(f"Downloading document {document.pk}")
            download_document.delay(document.pk)
