from django.db.models import Avg, Count, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from ..contracts.models import Contract, Contractor, Entity, Service, ServiceGroup
from ..contracts.utils import get_current_fiscal_year, get_fiscal_year_range
from ..utils.aggregates import Median
from .mixins import CachedAPIViewMixin
from .serializers import (
    ContractorSerializer,
    ContractSerializer,
    EntitySerializer,
    HomeSerializer,
    ServiceGroupSerializer,
    ServiceSerializer,
    SimpleContractSerializer,
)


def get_general_trend(fiscal_year):
    start_date, end_date = get_fiscal_year_range(fiscal_year)

    contracts = (
        Contract.objects.select_related("service", "service__group")
        .filter(effective_date_from__gte=start_date, effective_date_from__lte=end_date)
        .only("amount_to_pay", "service", "slug", "number")
        .order_by("amount_to_pay")
    )

    contracts_count = contracts.count()
    contracts_total = 0
    contracts_average = 0
    contractors_count = 0
    contracts_median = 0
    min_amount_to_pay_contract = 0
    max_amount_to_pay_contract = 0

    if contracts_count:
        min_amount_to_pay_contract = SimpleContractSerializer(contracts.first()).data
        max_amount_to_pay_contract = SimpleContractSerializer(contracts.last()).data

        stats = contracts.aggregate(
            total=Sum("amount_to_pay"),
            avg=Avg("amount_to_pay"),
            median=Median("amount_to_pay"),
        )

        contracts_total = stats["total"]
        contracts_median = stats["median"]
        contracts_average = stats["avg"]

        contractors_count = Contractor.objects.filter(contract__in=contracts).count()

    return {
        "fiscal_year": fiscal_year,
        "contract_max_amount": max_amount_to_pay_contract,
        "contract_min_amount": min_amount_to_pay_contract,
        "totals": [
            {"title": "Total de Contratos", "value": "{:,}".format(contracts_count)},
            {
                "title": "Monto Total de Contratos",
                "value": "${:,.2f}".format(contracts_total),
            },
            {
                "title": "Promedio Monto por Contrato",
                "value": "${:,.2f}".format(contracts_average),
            },
            {
                "title": "Media de Contratos",
                "value": "${:,.2f}".format(contracts_median),
            },
            {
                "title": "Total de Contratistas",
                "value": "{:,}".format(contractors_count),
            },
        ],
    }


def get_service_trend(fiscal_year):
    start_date, end_date = get_fiscal_year_range(fiscal_year)

    contracts = (
        Contract.objects.select_related("service", "service__group")
        .filter(effective_date_from__gte=start_date, effective_date_from__lte=end_date)
        .only("amount_to_pay", "service", "slug", "number")
        .order_by("amount_to_pay")
    )

    services = (
        Service.objects.filter(contract__in=contracts)
        .select_related("group")
        .annotate(contracts_total=Sum("contract__amount_to_pay"))
    )

    service_groups = ServiceGroup.objects.filter(
        service__contract__in=contracts
    ).annotate(contracts_total=Sum("service__contract__amount_to_pay"))

    service_totals = ServiceSerializer(services, many=True).data

    service_group_totals = ServiceGroupSerializer(service_groups, many=True).data

    return {
        "fiscal_year": fiscal_year,
        "services": {
            "title": "Totales por Tipos de Servicios",
            "value": service_totals,
        },
        "service_groups": {
            "title": "Totales por Categoria de Servicios",
            "value": service_group_totals,
        },
    }


class HomePageView(CachedAPIViewMixin, APIView):
    def get(self, request, format=None):
        serializer = HomeSerializer(data=request.GET)

        if serializer.is_valid():
            fiscal_year = serializer.validated_data.get(
                "fiscal_year", get_current_fiscal_year()
            )
        else:
            fiscal_year = get_current_fiscal_year() - 1

        start_date, end_date = get_fiscal_year_range(fiscal_year)

        contracts = (
            Contract.objects.without_amendments()
            .select_related(
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
            .filter(
                effective_date_from__gte=start_date, effective_date_from__lte=end_date
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
                "choices": [
                    choice for choice in serializer.fields["fiscal_year"].choices
                ],
            },
            "recent_contracts": recent_contracts_data,
            "contractors": contractors_data,
            "entities": entities_data,
            "contracts_count": contracts.count(),
            "contracts_total": contracts_total,
        }

        return Response(context)


class TrendsGeneralView(CachedAPIViewMixin, APIView):
    def get(self, request, format=None):
        current_fiscal_year = get_current_fiscal_year()

        fiscal_year = int(request.GET.get("fiscal_year", current_fiscal_year))

        return Response(
            {
                "a": get_general_trend(fiscal_year),
                "b": get_general_trend(fiscal_year - 1),
            }
        )


class TrendsServicesView(CachedAPIViewMixin, APIView):
    def get(self, request, format=None):
        current_fiscal_year = get_current_fiscal_year()

        fiscal_year = int(request.GET.get("fiscal_year", current_fiscal_year))

        return Response(
            {
                "a": get_service_trend(fiscal_year),
                "b": get_service_trend(fiscal_year - 1),
            }
        )
