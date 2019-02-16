import datetime
from collections import defaultdict

from django.utils import timezone


def get_current_fiscal_year():
    now = timezone.now()
    fiscal_year_end = timezone.make_aware(datetime.datetime(now.year, 6, 30))

    if now > fiscal_year_end:
        current_fiscal_year = now.year + 1
    else:
        current_fiscal_year = now.year

    return current_fiscal_year


def get_fiscal_year_range(fiscal_year):
    start_date = timezone.make_aware(datetime.datetime(fiscal_year, 7, 1))
    end_date = timezone.make_aware(datetime.datetime(fiscal_year + 1, 6, 30))

    return start_date, end_date


def get_chart_data(contracts):
    chart_data = []
    chart_data_groups = defaultdict(list)

    for contract in contracts:
        chart_data_groups[contract.date_of_grant.date()].append(contract.amount_to_pay)

    for date_of_grant, amounts in chart_data_groups.items():
        chart_data.append(
            {"x": date_of_grant, "y": sum(amounts), "contracts": len(amounts)}
        )

    return chart_data
