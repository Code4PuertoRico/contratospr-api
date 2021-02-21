from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..contracts.models import (
    CollectionJob,
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from ..contracts.utils import get_fiscal_year_range
from .filters import (
    ContractFilter,
    ContractorFilter,
    EntityFilter,
    NullsLastOrderingFilter,
    SearchQueryFilter,
    ServiceFilter,
    SimpleDjangoFilterBackend,
)
from .mixins import CachedAPIViewMixin
from .pagination import PageNumberPagination
from .schemas import CustomAutoSchema
from .serializers import (
    CollectionArtifactSerializer,
    CollectionJobSerializer,
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
    schema = CustomAutoSchema(tags=["contracts"])
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
        NullsLastOrderingFilter,
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

    @action(detail=False)
    def spending_over_time(self, request):
        fiscal_year = request.query_params.get("fiscal_year")

        queryset = self.filter_queryset(self.get_queryset())

        if fiscal_year:
            start_date, end_date = get_fiscal_year_range(int(fiscal_year))
            queryset = queryset.filter(
                date_of_grant__gte=start_date, date_of_grant__lte=end_date
            )

        queryset = (
            queryset.without_amendments()
            .annotate(month=TruncMonth("date_of_grant"))
            .values("month")
            .annotate(total=Sum("amount_to_pay"), count=Count("id"))
            .values("month", "total", "count")
            .order_by("month")
        )

        return Response(queryset)


class ContractorViewSet(CachedReadOnlyModelViewSet):
    schema = CustomAutoSchema(tags=["contractors"])
    queryset = Contractor.objects.all().annotate(
        contracts_total=Sum("contract__amount_to_pay"),
        contracts_count=Count("contract"),
    )
    serializer_class = ContractorSerializer
    filterset_class = ContractorFilter
    filter_backends = [
        NullsLastOrderingFilter,
        filters.SearchFilter,
        SimpleDjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["name", "contracts_count", "contracts_total"]
    ordering = ["name"]
    lookup_field = "slug"


class DocumentViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    schema = CustomAutoSchema(tags=["documents"])
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class EntityViewSet(CachedReadOnlyModelViewSet):
    schema = CustomAutoSchema(tags=["entities"])
    queryset = Entity.objects.all().annotate(
        contracts_total=Sum("contract__amount_to_pay"),
        contracts_count=Count("contract"),
    )
    serializer_class = EntitySerializer
    filterset_class = EntityFilter
    filter_backends = [
        NullsLastOrderingFilter,
        filters.SearchFilter,
        SimpleDjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"


class ServiceGroupViewSet(CachedReadOnlyModelViewSet):
    schema = CustomAutoSchema(tags=["service groups"])
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer
    filter_backends = [NullsLastOrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"


class ServiceViewSet(CachedReadOnlyModelViewSet):
    schema = CustomAutoSchema(tags=["services"])
    queryset = Service.objects.select_related("group")
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    filter_backends = [
        NullsLastOrderingFilter,
        filters.SearchFilter,
        SimpleDjangoFilterBackend,
    ]
    search_fields = ["name"]
    ordering_fields = ["name", "contracts_count", "contracts_total"]
    ordering = ["name"]
    lookup_field = "slug"


class CollectionJobViewSet(CachedReadOnlyModelViewSet):
    queryset = CollectionJob.objects.all()
    serializer_class = CollectionJobSerializer

    @action(detail=True, methods=["get"])
    def artifacts(self, request, pk=None):
        collection_job = self.get_object()
        queryset = collection_job.artifacts.all()
        model_type = request.query_params.get("type")

        if model_type:
            artifact_type = get_object_or_404(
                ContentType, app_label="contracts", model=model_type
            )
            queryset = collection_job.artifacts.filter(content_type=artifact_type)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, self.request, view=self)
        serializer = CollectionArtifactSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
