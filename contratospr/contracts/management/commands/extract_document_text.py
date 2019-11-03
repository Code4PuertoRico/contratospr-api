from django.core.management.base import BaseCommand

from ...models import Document
from ...tasks import detect_text


class Command(BaseCommand):
    help = "Extract text for the next N contract documents"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=1000)

    def handle(self, *args, **options):
        limit = options.get("limit")
        documents = (
            Document.objects.filter(pages__isnull=True)
            .exclude(file="")
            .order_by("modified_at")
            .only("pk")[:limit]
        )

        for document in documents:
            self.stdout.write(f"Detecting text for document {document.pk}")
            detect_text.delay(document.pk, modes=["pdf_to_text"])
