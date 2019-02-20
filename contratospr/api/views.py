from django.db.models import Count, Sum
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..contracts.models import (
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from ..contracts.utils import get_current_fiscal_year, get_fiscal_year_range
from ..contracts.views import HomeForm
from .filters import (
    ContractFilter,
    ContractorFilter,
    EntityFilter,
    SearchQueryFilter,
    ServiceFilter,
    SimpleDjangoFilterBackend,
)
from .schemas import ContractSchema
from .serializers import (
    ContractorSerializer,
    ContractSerializer,
    DocumentSerializer,
    EntitySerializer,
    ServiceGroupSerializer,
    ServiceSerializer,
)


@api_view(["GET"])
def homepage_api_view(request):
    form = HomeForm(request.GET) if request.method == "GET" else HomeForm()

    if form.is_valid():
        fiscal_year = form.cleaned_data.get("fiscal_year", get_current_fiscal_year())
    else:
        fiscal_year = get_current_fiscal_year() - 1

    start_date, end_date = get_fiscal_year_range(fiscal_year)

    contracts = (
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
        .filter(
            parent=None,
            effective_date_from__gte=start_date,
            effective_date_from__lte=end_date,
        )
    )

    contracts_total = contracts.aggregate(total=Sum("amount_to_pay"))["total"]

    recent_contracts = contracts.order_by("-effective_date_from")[:5]

    contractors = (
        Contractor.objects.prefetch_related("contract_set")
        .filter(
            contract__parent=None,
            contract__effective_date_from__gte=start_date,
            contract__effective_date_from__lte=end_date,
        )
        .annotate(
            contracts_total=Sum("contract__amount_to_pay"),
            contracts_count=Count("contract"),
        )
        .order_by("-contracts_total")
    )[:5]

    entities = (
        Entity.objects.prefetch_related("contract_set")
        .filter(
            contract__parent=None,
            contract__effective_date_from__gte=start_date,
            contract__effective_date_from__lte=end_date,
        )
        .annotate(
            contracts_total=Sum("contract__amount_to_pay"),
            contracts_count=Count("contract"),
        )
        .order_by("-contracts_total")
    )[:5]

    serializer_context = {"request": request}
    recent_contracts_data = ContractSerializer(
        recent_contracts, context=serializer_context, many=True
    ).data

    contractors_data = ContractorSerializer(
        contractors, context=serializer_context, many=True
    ).data

    entities_data = EntitySerializer(
        entities, context=serializer_context, many=True
    ).data

    context = {
        "fiscal_year": {
            "current": fiscal_year,
            "choices": [choice[0] for choice in form.fields["fiscal_year"].choices],
        },
        "recent_contracts": recent_contracts_data,
        "contractors": contractors_data,
        "entities": entities_data,
        "contracts_count": contracts.count(),
        "contracts_total": contracts_total,
    }

    return Response(context)


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
    lookup_field = "slug"


class ContractorViewSet(viewsets.ReadOnlyModelViewSet):
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


class EntityViewSet(viewsets.ReadOnlyModelViewSet):
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


class ServiceGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    lookup_field = "slug"


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
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
