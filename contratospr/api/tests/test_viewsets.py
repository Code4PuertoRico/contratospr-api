from unittest import mock

from django.core.files import File
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.views import status

from contratospr.contracts import models


class TestContractViewSet(APITestCase):
    def test_viewset_list_url(self):
        url = reverse("v1:contract-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestContractorViewSet(APITestCase):
    def test_viewset_list_url(self):
        url = reverse("v1:contractor-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestDocumentViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = "test_file.pdf"
        cls.test_document = models.Document(file=file_mock, source_id=1)
        cls.test_document.save()

    def test_viewset_detail_url(self):
        url = reverse("v1:document-detail", args=[self.test_document.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestEntityViewSet(APITestCase):
    def test_viewset_list_url(self):
        url = reverse("v1:entity-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_obtain_instance(self):
        entity = models.Entity(name="Test Entity", source_id=1)
        entity.save()
        url = reverse("v1:entity-detail", args=[entity.slug])
        response = self.client.get(url)
        for key in ("contracts_total", "contracts_count"):
            self.assertIn(key, response.data)


class TestServiceGroupViewSet(APITestCase):
    def test_viewset_list_url(self):
        url = reverse("v1:servicegroup-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestServiceViewSet(APITestCase):
    def test_viewset_list_url(self):
        url = reverse("v1:service-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
