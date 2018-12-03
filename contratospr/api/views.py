from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets

from ..contracts.models import (
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from .filters import ContractFilter, SearchQueryFilter, SimpleDjangoFilterBackend
from .schemas import ContractSchema
from .serializers import (
    ContractorSerializer,
    ContractSerializer,
    DocumentSerializer,
    EntitySerializer,
    ServiceGroupSerializer,
    ServiceSerializer,
)


class ContractViewSet(viewsets.ReadOnlyModelViewSet):
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
        .prefetch_related("contractors", "parent__contractors")
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


class ContractorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contractor.objects.all()
    serializer_class = ContractorSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class DocumentViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class ServiceGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.select_related("group").all()
    serializer_class = ServiceSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["name", "group"]
    ordering_fields = ["name"]
    ordering = ["name"]
