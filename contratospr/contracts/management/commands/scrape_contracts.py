from django.core.management.base import BaseCommand

from ...tasks import scrape_contracts


class Command(BaseCommand):
    help = "Scrape search results"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=None)
        parser.add_argument("--effective-start", nargs="?", type=str, default=None)
        parser.add_argument("--effective-end", nargs="?", type=str, default=None)

    def handle(self, *args, **options):
        scrape_contracts.send(
            limit=options["limit"],
            effective_start=options["effective_start"],
            effective_end=options["effective_end"],
        )
