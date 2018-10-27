import cgi
import json
from tempfile import TemporaryFile

import requests
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.files import File
from django.db import models
from django_s3_storage.storage import S3Storage
from filepreviews import FilePreviews
from google.cloud import vision
from google.oauth2.service_account import Credentials
from google.protobuf.json_format import MessageToDict

from ..utils.models import BaseModel

service_account_info = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS)
credentials = Credentials.from_service_account_info(service_account_info)

s3_storage = S3Storage()


def get_filename_from_content_disposition(value):
    _, parsed_header = cgi.parse_header(value)
    return parsed_header.get("filename", "")


def document_file_path(instance, filename):
    return f"documents/{instance.source_id}/{filename}"


class Entity(BaseModel):
    name = models.CharField(max_length=255)
    source_id = models.PositiveIntegerField(unique=True)

    class Meta:
        verbose_name_plural = "Entities"

    def __str__(self):
        return self.name


class Service(BaseModel):
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=255)

    class Meta:
        unique_together = ("name", "group")

    def __str__(self):
        return self.name


class Document(BaseModel):
    source_id = models.PositiveIntegerField(unique=True)
    source_url = models.URLField()
    file = models.FileField(
        blank=True, null=True, upload_to=document_file_path, storage=s3_storage
    )

    preview_data = JSONField(blank=True, null=True)
    vision_data = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.source_id}"

    @property
    def text(self):
        pages = []

        if self.vision_data:
            for result in self.vision_data:
                pages.append(
                    {
                        "page": result["page"],
                        "text": result["fullTextAnnotation"]["text"],
                    }
                )
        elif self.preview_data:
            original_file = self.preview_data["original_file"] or {
                "metadata": {"ocr": []}
            }

            for result in original_file["metadata"]["ocr"]:
                pages.append({"page": result["page"], "text": result["text"]})

        return pages

    def download(self):
        with TemporaryFile() as temp_file:
            with requests.get(self.source_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    temp_file.write(chunk)
                temp_file.seek(0)

            content_disposition = r.headers.get("content-disposition", "")
            file_name = get_filename_from_content_disposition(content_disposition)

            self.file.save(file_name, File(temp_file))

    def generate_preview(self):
        if self.file:
            fp = FilePreviews(
                api_key=settings.FILEPREVIEWS_API_KEY,
                api_secret=settings.FILEPREVIEWS_API_SECRET,
            )

            response = fp.generate(
                self.file.url,
                pages="all",
                metadata=["ocr"],
                data={"document_id": self.pk},
                uploader={"public": True},
            )

            self.preview_data = response
            self.save(update_fields=["preview_data"])

    def detect_text(self):
        if self.preview_data:
            client = vision.ImageAnnotatorClient(credentials=credentials)
            responses = []

            for thumbnail in self.preview_data["thumbnails"]:
                image = vision.types.Image()
                image.source.image_uri = thumbnail["url"]
                response = client.document_text_detection(image=image)
                response_dict = MessageToDict(response)
                response_dict["page"] = thumbnail["page"]
                responses.append(response_dict)

            self.vision_data = responses
            self.save(update_fields=["vision_data"])


class Contractor(BaseModel):
    name = models.CharField(max_length=255)
    source_id = models.PositiveIntegerField(unique=True)
    entity_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class Contract(BaseModel):
    entity = models.ForeignKey("Entity", null=True, on_delete=models.SET_NULL)
    source_id = models.PositiveIntegerField(unique=True)
    number = models.CharField(max_length=255)
    amendment = models.CharField(max_length=255, blank=True, null=True)
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

    def __str__(self):
        if self.amendment:
            return f"{self.number} - {self.amendment}"

        return f"{self.number}"
