from django.db import models

from .queryset import ContractQuerySet


class BaseContractManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().defer("search_vector")


ContractManager = BaseContractManager.from_queryset(ContractQuerySet)
