from django.db.models import Count, Sum
from rest_framework import filters, mixins, viewsets

from ..contracts.models import (
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from .filters import (
    ContractFilter,
    ContractorFilter,
    EntityFilter,
    SearchQueryFilter,
    ServiceFilter,
    SimpleDjangoFilterBackend,
)
from .mixins import CachedAPIViewMixin
from .schemas import ContractSchema
from .serializers import (
    ContractorSerializer,
    ContractSerializer,
    DocumentSerializer,
    EntitySerializer,
    ServiceGroupSerializer,
    ServiceSerializer,
)


class CachedReadOnlyModelViewSet(CachedAPIViewMixin, viewsets.ReadOnlyModelViewSet):
    pass


class ContractViewSet(CachedReadOnlyModelViewSet):
    schema = ContractSchema()
    queryset = (
        Contract.objects.select_related(
            "document",
            "entity",
            "service",
            "service__group",
            "parent__document",
            "parent__entity",
            "parent__service",
            "parent__service__group",
        )
        .prefetch_related(
            "contractors", "parent__contractors", "amendments", "parent__amendments"
        )
        .all()
    )
    serializer_class = ContractSerializer
    filter_backends = [
        SearchQueryFilter,
        SimpleDjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_class = ContractFilter
    ordering_fields = [
        "amount_to_pay",
        "date_of_grant",
        "effective_date_from",
        "effective_date_to",
        "created_at",
        "modified_at",
    ]
    ordering = ["-date_of_grant"]
    lookup_field = "slug"


class ContractorViewSet(CachedReadOnlyModelViewSet):
    queryset = Contractor.objects.all().annotate(
        contracts_total=Sum("contract__amount_to_pay"),
        contracts_count=Count("contract"),
    )
    serializer_class = ContractorSerializer
    filterset_class = ContractorFilter
    filter_backends = [
        filters.OrderingFilter,
        filters.SearchFilter,
        SimpleDjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"


class DocumentViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class EntityViewSet(CachedReadOnlyModelViewSet):
    queryset = Entity.objects.all().annotate(
        contracts_total=Sum("contract__amount_to_pay"),
        contracts_count=Count("contract"),
    )
    serializer_class = EntitySerializer
    filterset_class = EntityFilter
    filter_backends = [
        filters.OrderingFilter,
        filters.SearchFilter,
        SimpleDjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"


class ServiceGroupViewSet(CachedReadOnlyModelViewSet):
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"


class ServiceViewSet(CachedReadOnlyModelViewSet):
    queryset = Service.objects.select_related("group").all()
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    filter_backends = [
        filters.OrderingFilter,
        filters.SearchFilter,
        SimpleDjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"
