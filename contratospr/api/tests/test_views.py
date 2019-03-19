from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.views import status


class TestViews(APITestCase):
    def test_root_view_url(self):
        url = reverse("v1:api-root")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_home_page_view_url(self):
        response = self.client.get("/v1/pages/home/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_home_page_view_response(self):
        response = self.client.get("/v1/pages/home/")

        for key in (
            "fiscal_year",
            "recent_contracts",
            "contractors",
            "entities",
            "contracts_count",
            "contracts_total",
        ):
            self.assertIn(key, response.data)

    def test_trends_general_view_url(self):
        response = self.client.get("/v1/pages/trends/general/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_test_trends_services_view_url(self):
        response = self.client.get("/v1/pages/trends/services/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
