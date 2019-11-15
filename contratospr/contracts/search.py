from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models.functions import Cast

from .models import Contract

search_config = "spanish_unaccent"
search_vector = (
    SearchVector(Cast("document__pages", JSONField()), config=search_config)
    + SearchVector("contractors__name", config=search_config)
    + SearchVector("entity__name", config=search_config)
    + SearchVector("number", config=search_config)
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


def search_contracts(query, service_id, service_group_id):
    filter_kwargs = {}

    if query:
        filter_kwargs["search_vector"] = SearchQuery(query, config=search_config)

    if service_id:
        filter_kwargs["service_id"] = service_id

    if service_group_id:
        filter_kwargs["service__group_id"] = service_group_id

    if not filter_kwargs:
        return []

    return (
        Contract.objects.select_related("document", "entity", "service")
        .prefetch_related("contractors")
        .defer(
            "document__pages",
            "document__preview_data_file",
            "document__vision_data_file",
        )
        .filter(**filter_kwargs)
        .order_by("-date_of_grant")
    )
