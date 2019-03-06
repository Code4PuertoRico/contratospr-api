from django.core.management.base import BaseCommand

from ...tasks import scrape_contracts


class Command(BaseCommand):
    help = "Scrape search results"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=None)
        parser.add_argument("--date-of-grant-start", nargs="?", type=str, default=None)
        parser.add_argument("--date-of-grant-end", nargs="?", type=str, default=None)
        parser.add_argument("--entity-id", nargs="?", type=str, default=None)
        parser.add_argument("--contract-number", nargs="?", type=str, default=None)
        parser.add_argument("--contractor-name", nargs="?", type=str, default=None)
        parser.add_argument("--effective-date-start", nargs="?", type=str, default=None)
        parser.add_argument("--effective-date-end", nargs="?", type=str, default=None)
        parser.add_argument("--amount-from", nargs="?", type=str, default=None)
        parser.add_argument("--amount-to", nargs="?", type=str, default=None)
        parser.add_argument("--service-group-id", nargs="?", type=str, default=None)
        parser.add_argument("--service-id", nargs="?", type=str, default=None)

    def handle(self, *args, **options):
        limit = options.pop("limit", None)
        scrape_contracts.delay(limit=limit, **options)
