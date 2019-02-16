from django.core.management.base import BaseCommand

from ...tasks import scrape_contracts


class Command(BaseCommand):
    help = "Scrape search results"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=None)
        parser.add_argument("--date-of-grant-start", nargs="?", type=str, default=None)
        parser.add_argument("--date-of-grant-end", nargs="?", type=str, default=None)

    def handle(self, *args, **options):
        scrape_contracts.send(
            limit=options["limit"],
            date_of_grant_start=options["date_of_grant_start"],
            date_of_grant_end=options["date_of_grant_end"],
        )
