import datetime

from django.utils import timezone

from ..utils import get_current_fiscal_year, get_fiscal_year_range


class TestUtils:
    def test_get_current_fiscal_year(self):
        now = timezone.now()
        fiscal_year_end = timezone.make_aware(datetime.datetime(now.year, 6, 30))

        current_fiscal_year = get_current_fiscal_year()

        if now > fiscal_year_end:
            assert current_fiscal_year == now.year + 1
        else:
            assert current_fiscal_year == now.year

    def test_get_fiscal_year_range(self):
        start, end = get_fiscal_year_range(2019)
        assert start == timezone.make_aware(datetime.datetime(2018, 7, 1))
        assert end == timezone.make_aware(datetime.datetime(2019, 6, 30))
