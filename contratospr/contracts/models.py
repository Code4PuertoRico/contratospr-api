from django.db import models

from ..utils.models import BaseModel


class Entity(BaseModel):
    name = models.CharField(max_length=255)
    source_id = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return self.name


class Service(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    group = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Document(BaseModel):
    source_id = models.PositiveIntegerField(unique=True)
    source_url = models.URLField()
    file = models.FileField(blank=True, null=True)

    def __str__(self):
        return f"{self.source_id}"


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
