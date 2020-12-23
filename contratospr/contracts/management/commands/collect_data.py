from django.core.management.base import BaseCommand

from ...tasks import collect_data


class Command(BaseCommand):
    help = "Scrape search results"

    def add_arguments(self, parser):
        parser.add_argument("--date-of-grant-start", nargs="?", type=str, default=None)
        parser.add_argument("--date-of-grant-end", nargs="?", type=str, default=None)

    def handle(self, *args, **options):
        collect_data.delay(
            date_of_grant_start=options["date_of_grant_start"],
            date_of_grant_end=options["date_of_grant_end"],
        )
