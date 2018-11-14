from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchQuery
from django.db.models.functions import Cast

from ..utils.search import SearchVector
from .models import Contract

search_vector = (
    SearchVector(Cast("document__pages", JSONField()))
    + SearchVector("contractors__name")
    + SearchVector("entity__name")
)


def index_contract(obj):
    instance = (
        Contract.objects.select_related("document", "entity")
        .prefetch_related("contractors")
        .annotate(search=search_vector)
        .filter(pk=obj.pk)
    )[:1]

    contract = instance[0]
    contract.search_vector = contract.search
    return contract.save(update_fields=["search_vector"])


def search_contracts(query):
    return (
        Contract.objects.select_related("document")
        .prefetch_related("contractors")
        .annotate(search=search_vector)
        .filter(search=SearchQuery(query))
    )
