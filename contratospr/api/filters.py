import coreapi
import coreschema
from django.contrib.postgres.search import SearchQuery
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

    service = django_filters.ModelChoiceFilter(
        help_text="Filter by Service ID", queryset=Service.objects.all()
    )

    service_group = django_filters.ModelChoiceFilter(
        field_name="service__group",
        help_text="Filter by Service Group ID",
        queryset=ServiceGroup.objects.all(),
    )

    entity = django_filters.ModelChoiceFilter(
        help_text="Filter by Entity ID", queryset=Entity.objects.all()
    )

    contractor = django_filters.ModelChoiceFilter(
        field_name="contractors",
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
    )

    class Meta:
        model = Contract
        fields = ["number", "service", "service_group", "entity", "contractor"]


class ContractorFilter(django_filters.FilterSet):
    entity = django_filters.ModelChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all(),
        method="filter_entity",
    )

    class Meta:
        model = Contractor
        fields = ["entity"]

    def filter_entity(self, queryset, name, value):
        contracts = value.contract_set.all()
        return queryset.filter(contract__in=contracts).distinct()


class EntityFilter(django_filters.FilterSet):
    contractor = django_filters.ModelChoiceFilter(
        help_text="Filter by Contractgor ID",
        queryset=Contractor.objects.all(),
        method="filter_contractor",
    )

    class Meta:
        model = Entity
        fields = ["contractor"]

    def filter_contractor(self, queryset, name, value):
        contracts = value.contract_set.filter(parent=None)
        return queryset.filter(contract__in=contracts).distinct()


class ServiceFilter(django_filters.FilterSet):
    contractor = django_filters.ModelChoiceFilter(
        field_name="contractor",
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
        method="filter_contractor",
    )

    class Meta:
        model = Service
        fields = ["group", "contractor"]

    def filter_contractor(self, queryset, name, value):
        contracts = value.contract_set.filter(parent=None)
        return queryset.filter(
            pk__in=[contract.service_id for contract in contracts]
        ).distinct()
