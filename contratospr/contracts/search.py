from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchQuery
from django.db.models.functions import Cast

from ..utils.search import SearchVector
from .models import Contract

search_vector = SearchVector(Cast("document__pages", JSONField())) + SearchVector(
    "contractors__name"
)


def index_contract(obj):
    instance = (
        Contract.objects.select_related("document")
        .prefetch_related("contractors")
        .annotate(search=search_vector)
        .get(pk=obj.pk)
    )

    instance.search_vector = instance.search
    return instance.save(update_fields=["search_vector"])


def search_contracts(query):
    return (
        Contract.objects.select_related("document")
        .prefetch_related("contractors")
        .annotate(search=search_vector)
        .filter(search=SearchQuery(query))
    )
