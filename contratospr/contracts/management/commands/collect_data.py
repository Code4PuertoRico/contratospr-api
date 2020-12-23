from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from ...models import CollectionJob


class Command(BaseCommand):
    help = "Scrape search results"

    def add_arguments(self, parser):
        parser.add_argument("--date-of-grant-start", nargs="?", type=str, default=None)
        parser.add_argument("--date-of-grant-end", nargs="?", type=str, default=None)

    def handle(self, *args, **options):
        now = datetime.utcnow()

        if options["date_of_grant_start"]:
            date_of_grant_start = date.fromisoformat(options["date_of_grant_start"])
        else:
            date_of_grant_start = now + relativedelta(
                months=-1, day=1, hour=0, minute=0, second=0, microsecond=0
            )

        if options["date_of_grant_end"]:
            date_of_grant_end = date.fromisoformat(options["date_of_grant_end"])
        else:
            date_of_grant_end = (
                now
                + relativedelta(
                    months=-1, day=1, hour=0, minute=0, second=0, microsecond=0
                )
                + relativedelta(months=+1, days=-1)
            )

        job = CollectionJob.objects.create(
            date_of_grant_start=date_of_grant_start, date_of_grant_end=date_of_grant_end
        )
        job.process()
