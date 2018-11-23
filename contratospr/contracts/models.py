import cgi
import json
from tempfile import TemporaryFile

import requests
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.files import File
from django.db import models
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django_extensions.db.fields import AutoSlugField
from filepreviews import FilePreviews
from google.cloud import vision
from google.oauth2.service_account import Credentials
from google.protobuf.json_format import MessageToDict

from ..utils.models import BaseModel

if settings.FILEPREVIEWS_API_KEY and settings.FILEPREVIEWS_API_SECRET:
    filepreviews = FilePreviews(
        api_key=settings.FILEPREVIEWS_API_KEY,
        api_secret=settings.FILEPREVIEWS_API_SECRET,
    )
else:
    filepreviews = None

service_account_info = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS)
credentials = Credentials.from_service_account_info(service_account_info)

document_storage = import_string(settings.CONTRACTS_DOCUMENT_STORAGE)()


def get_filename_from_content_disposition(value):
    _, parsed_header = cgi.parse_header(value)
    return parsed_header.get("filename", "")


def document_file_path(instance, filename):
    return f"documents/{instance.source_id}/{filename}"


class Entity(BaseModel):
    name = models.CharField(max_length=255)
    source_id = models.PositiveIntegerField(unique=True)
    slug = AutoSlugField(populate_from="name")

    class Meta:
        verbose_name_plural = "Entities"

    def __str__(self):
        return self.name

    @property
    def contracts_count(self):
        return self.contract_set.count()

    @property
    def contracts_total(self):
        return sum([contract.amount_to_pay for contract in self.contract_set.all()])


class ServiceGroup(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="name")

    def __str__(self):
        return self.name


class Service(BaseModel):
    name = models.CharField(max_length=255)
    group = models.ForeignKey("ServiceGroup", null=True, on_delete=models.SET_NULL)
    slug = AutoSlugField(populate_from="name")

    class Meta:
        unique_together = ("name", "group")

    def __str__(self):
        return self.name


class Document(BaseModel):
    source_id = models.PositiveIntegerField(unique=True)
    source_url = models.URLField()
    file = models.FileField(
        blank=True, null=True, upload_to=document_file_path, storage=document_storage
    )

    pages = JSONField(blank=True, null=True)

    preview_data_file = models.FileField(
        blank=True, null=True, upload_to=document_file_path, storage=document_storage
    )

    vision_data_file = models.FileField(
        blank=True, null=True, upload_to=document_file_path, storage=document_storage
    )

    def __str__(self):
        return f"{self.source_id}"

    @cached_property
    def preview_data(self):
        if self.preview_data_file:
            with self.preview_data_file.open() as preview_data_file:
                preview_data = json.load(preview_data_file)
            return preview_data

    @cached_property
    def vision_data(self):
        if self.vision_data_file:
            with self.vision_data_file.open() as vision_data_file:
                vision_data = json.load(vision_data_file)
            return vision_data

    def download(self):
        with TemporaryFile() as temp_file:
            with requests.get(self.source_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    temp_file.write(chunk)
                temp_file.seek(0)

            content_disposition = r.headers.get("content-disposition", "")
            file_name = get_filename_from_content_disposition(content_disposition)

            self.file.save(file_name, File(temp_file))

    def update_preview_data(self, data):
        with TemporaryFile() as temp_file:
            temp_file.write(json.dumps(data).encode("utf-8"))
            temp_file.seek(0)

            self.preview_data_file.save("preview.json", File(temp_file), save=False)

    def update_vision_data(self, data):
        with TemporaryFile() as temp_file:
            temp_file.write(json.dumps(data).encode("utf-8"))
            temp_file.seek(0)

            self.vision_data_file.save("vision.json", File(temp_file), save=False)

    def generate_preview(self):
        if self.file and filepreviews:
            response = filepreviews.generate(
                self.file.url,
                pages="all",
                metadata=["ocr"],
                data={"document_id": self.pk},
                uploader={"public": True},
            )

            self.update_preview_data(response)
            self.save(update_fields=["preview_data_file"])

    def detect_text(self):
        if self.preview_data and self.preview_data["thumbnails"]:
            client = vision.ImageAnnotatorClient(credentials=credentials)
            results = []
            pages = []

            for thumbnail in self.preview_data["thumbnails"]:
                image = vision.types.Image()
                image.source.image_uri = thumbnail["url"]
                response = client.document_text_detection(image=image)
                result = MessageToDict(response)
                result["page"] = thumbnail["page"]
                results.append(result)

                full_text_annotation = result.get("fullTextAnnotation")
                text_annotations = result.get("textAnnotations")

                if full_text_annotation:
                    pages.append(
                        {"number": result["page"], "text": full_text_annotation["text"]}
                    )
                elif text_annotations:
                    pages.append(
                        {
                            "number": result["page"],
                            "text": text_annotations[0]["description"],
                        }
                    )

            self.pages = pages
            self.update_vision_data(results)
            self.save(update_fields=["vision_data_file", "pages"])


class Contractor(BaseModel):
    name = models.CharField(max_length=255)
    source_id = models.PositiveIntegerField(unique=True)
    entity_id = models.PositiveIntegerField(blank=True, null=True)
    slug = AutoSlugField(populate_from=["name", "source_id"])

    def __str__(self):
        return self.name

    @property
    def contracts_count(self):
        return self.contract_set.count()

    @property
    def contracts_total(self):
        return sum([contract.amount_to_pay for contract in self.contract_set.all()])


class Contract(BaseModel):
    entity = models.ForeignKey("Entity", null=True, on_delete=models.SET_NULL)
    source_id = models.PositiveIntegerField(unique=True)
    number = models.CharField(max_length=255)
    amendment = models.CharField(max_length=255, blank=True, null=True)
    slug = AutoSlugField(populate_from=["number", "amendment", "source_id"])
    date_of_grant = models.DateTimeField()
    effective_date_from = models.DateTimeField()
    effective_date_to = models.DateTimeField()
    service = models.ForeignKey("Service", null=True, on_delete=models.SET_NULL)
    cancellation_date = models.DateTimeField(blank=True, null=True)
    amount_to_pay = models.DecimalField(max_digits=20, decimal_places=2)
    has_amendments = models.BooleanField()
    document = models.ForeignKey("Document", null=True, on_delete=models.SET_NULL)
    exempt_id = models.CharField(max_length=255)
    contractors = models.ManyToManyField("Contractor")
    parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)

    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [GinIndex(fields=["search_vector"])]

    def __str__(self):
        if self.amendment:
            return f"{self.number} - {self.amendment}"

        return f"{self.number}"

    @property
    def amendments(self):
        return Contract.objects.filter(parent=self)
