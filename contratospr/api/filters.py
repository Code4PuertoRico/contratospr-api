import coreapi
import coreschema
from django.contrib.postgres.search import SearchQuery
from django.db.models import Count, Q, Sum
from django.template import loader
from django_filters import rest_framework as django_filters
from rest_framework.filters import BaseFilterBackend

from ..contracts.models import Contract, Contractor, Entity, Service, ServiceGroup


class SimpleDjangoFilterBackend(django_filters.DjangoFilterBackend):
    def to_html(self, *args, **kwargs):
        # Prevent large dropdowns from being rendered in Browsable API
        return ""


class SearchQueryFilter(BaseFilterBackend):
    template = "rest_framework/filters/search.html"
    search_param = "search"

    def get_search_term(self, request):
        return request.query_params.get(self.search_param)

    def filter_queryset(self, request, queryset, view):
        search_term = self.get_search_term(request)

        if not search_term:
            return queryset

        return queryset.filter(search_vector=SearchQuery(search_term))

    def to_html(self, request, queryset, view):
        search_term = self.get_search_term(request) or ""
        template = loader.get_template(self.template)
        return template.render({"param": self.search_param, "term": search_term})

    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name=self.search_param,
                required=False,
                location="query",
                schema=coreschema.String(title="Search", description="A search term."),
            )
        ]


class ContractFilter(django_filters.FilterSet):
    number = django_filters.CharFilter(help_text="Filter by Contract number")

    service_id = django_filters.ModelChoiceFilter(
        help_text="Filter by Service ID", queryset=Service.objects.all()
    )

    service_group_id = django_filters.ModelChoiceFilter(
        field_name="service__group",
        help_text="Filter by Service Group ID",
        queryset=ServiceGroup.objects.all(),
    )

    entity_id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID", queryset=Entity.objects.all()
    )

    contractor_name = django_filters.CharFilter(
        help_text="Filter by Contractor name", method="filter_contractors_by_name"
    )

    contractor_id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all().only("id"),
        method="filter_contractors_by_id",
    )

    date_of_grant = django_filters.DateFromToRangeFilter()

    exclude_amendments = django_filters.BooleanFilter(
        method="filter_exclude_amendments"
    )

    class Meta:
        model = Contract
        fields = [
            "number",
            "service_id",
            "service_group_id",
            "entity_id",
            "contractor_name",
            "contractor_id",
            "date_of_grant",
            "has_amendments",
        ]

    def filter_contractors_by_name(self, queryset, name, value):
        if not value:
            return queryset

        contractors = Contractor.objects.filter(name__icontains=value).only("id")
        return queryset.filter(contractors__in=contractors)

    def filter_contractors_by_id(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(contractors__in=value)

    def filter_exclude_amendments(self, queryset, name, value):
        if value is True:
            return queryset.filter(parent__isnull=True)

        return queryset


class ContractorFilter(django_filters.FilterSet):
    id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all().only("id"),
        method="filter_contractors",
    )

    entity_id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all(),
        method="filter_entities",
    )

    class Meta:
        model = Contractor
        fields = ["id", "entity_id"]

    def filter_contractors(self, queryset, name, value):
        if not value:
            return queryset

        contractor_ids = [contractor.id for contractor in value]
        return queryset.filter(pk__in=contractor_ids)

    def filter_entities(self, queryset, name, value):
        if not value:
            return queryset
        return (
            queryset.filter(contract__entity__in=value)
            .distinct()
            .annotate(
                contracts_total=Sum(
                    "contract__amount_to_pay",
                    filter=Q(contract__parent=None, contract__entity__in=value),
                ),
                contracts_count=Count(
                    "contract",
                    filter=Q(contract__parent=None, contract__entity__in=value),
                ),
            )
        )


class EntityFilter(django_filters.FilterSet):
    id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all().only("id"),
        method="filter_entities",
    )

    contractor_id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
        method="filter_contractors_by_id",
    )
    # source_id = django_filters.NumberFilter()
    source_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Entity.objects.all().only("source_id"),
        method="filter_entities_source_id",
    )

    class Meta:
        model = Entity
        fields = ["id", "contractor_id", "source_id"]

    def filter_entities(self, queryset, name, value):
        if not value:
            return queryset

        entity_ids = [entity.id for entity in value]
        return queryset.filter(pk__in=entity_ids)

    def filter_contractors_by_id(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(contract__contractors__in=value).distinct()

    def filter_entities_source_id(self, queryset, name, value):
        if not value:
            return queryset

        source_ids = [entity.source_id for entity in value]
        return queryset.filter(source_id__in=source_ids)


class ServiceFilter(django_filters.FilterSet):
    id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Service ID",
        queryset=Service.objects.all().only("id"),
        method="filter_services",
    )

    entity_id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all(),
        method="filter_entity_by_id",
    )

    contractor_id = django_filters.ModelMultipleChoiceFilter(
        field_name="contractor",
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
        method="filter_contractors_by_id",
    )

    class Meta:
        model = Service
        fields = ["id", "entity_id", "group_id", "contractor_id"]

    def filter_services(self, queryset, name, value):
        if not value:
            return queryset

        service_ids = [service.id for service in value]
        return queryset.filter(pk__in=service_ids)

    def filter_entity_by_id(self, queryset, name, value):
        if not value:
            return queryset

        contracts = Contract.objects.filter(entity__in=value).only("id")

        return (
            queryset.filter(contract__in=contracts)
            .distinct()
            .annotate(
                contracts_total=Sum(
                    "contract__amount_to_pay",
                    filter=Q(contract__parent=None, contract__in=contracts),
                ),
                contracts_count=Count(
                    "contract", filter=Q(contract__parent=None, contract__in=contracts)
                ),
            )
        )

    def filter_contractors_by_id(self, queryset, name, value):
        if not value:
            return queryset

        contracts = Contract.objects.filter(contractors__in=value).only("id")

        return (
            queryset.filter(contract__in=contracts)
            .distinct()
            .annotate(
                contracts_total=Sum(
                    "contract__amount_to_pay",
                    filter=Q(contract__parent=None, contract__in=contracts),
                ),
                contracts_count=Count(
                    "contract", filter=Q(contract__parent=None, contract__in=contracts)
                ),
            )
        )
