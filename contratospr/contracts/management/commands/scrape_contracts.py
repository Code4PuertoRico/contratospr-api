from django.core.management.base import BaseCommand

from ...tasks import scrape_contracts


class Command(BaseCommand):
    help = "Scrape search results"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=100)

    def handle(self, *args, **options):
        scrape_contracts.send(options["limit"])
