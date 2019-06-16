import coreapi
import coreschema
from django.contrib.postgres.search import SearchQuery
from django.db.models import Count, Q, Sum
from django.template import loader
from django_filters import rest_framework as django_filters
from rest_framework.filters import BaseFilterBackend

from ..contracts.models import Contract, Contractor, Entity, Service, ServiceGroup
from ..contracts.utils import get_fiscal_year_range

FISCAL_YEAR_CHOICES = [(2016, "2016"), (2017, "2017"), (2018, "2018"), (2019, "2019")]


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

    entity = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID", queryset=Entity.objects.all()
    )

    contractor = django_filters.ModelMultipleChoiceFilter(
        field_name="contractors",
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
    )

    fiscal_year = django_filters.TypedChoiceFilter(
        choices=FISCAL_YEAR_CHOICES, coerce=int, method="filter_fiscal_year"
    )

    date_of_grant = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Contract
        fields = [
            "number",
            "service",
            "service_group",
            "entity",
            "contractor",
            "fiscal_year",
            "date_of_grant",
        ]

    def filter_fiscal_year(self, queryset, name, value):
        if not value:
            return queryset

        start_date, end_date = get_fiscal_year_range(value)
        return queryset.filter(
            effective_date_from__gte=start_date, effective_date_from__lte=end_date
        )


class ContractorFilter(django_filters.FilterSet):
    id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all().only("id"),
        method="filter_contractors",
    )

    entity = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all(),
        method="filter_entities",
    )

    fiscal_year = django_filters.TypedChoiceFilter(
        choices=FISCAL_YEAR_CHOICES, coerce=int, method="filter_fiscal_year"
    )

    class Meta:
        model = Contractor
        fields = ["id", "entity", "fiscal_year"]

    def filter_contractors(self, queryset, name, value):
        if not value:
            return queryset

        contractor_ids = [contractor.id for contractor in value]
        return queryset.filter(pk__in=contractor_ids)

    def filter_entities(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(contract__entity__in=value).distinct()

    def filter_fiscal_year(self, queryset, name, value):
        # TODO This should probably be done in .qs
        if not value:
            return queryset

        start_date, end_date = get_fiscal_year_range(value)
        fiscal_year_filter = Q(contract__effective_date_from__gte=start_date) & Q(
            contract__effective_date_from__lte=end_date
        )
        return queryset.annotate(
            contracts_total=Sum("contract__amount_to_pay", filter=fiscal_year_filter),
            contracts_count=Count("contract", filter=fiscal_year_filter),
        )


class EntityFilter(django_filters.FilterSet):
    id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all().only("id"),
        method="filter_entities",
    )

    contractor = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
        method="filter_contractor",
    )

    fiscal_year = django_filters.TypedChoiceFilter(
        choices=FISCAL_YEAR_CHOICES, coerce=int, method="filter_fiscal_year"
    )

    class Meta:
        model = Entity
        fields = ["id", "contractor", "fiscal_year"]

    def filter_entities(self, queryset, name, value):
        if not value:
            return queryset

        entity_ids = [entity.id for entity in value]
        return queryset.filter(pk__in=entity_ids)

    def filter_contractor(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            contract__contractors__in=value, contract__parent=None
        ).distinct()

    def filter_fiscal_year(self, queryset, name, value):
        # TODO This should probably be done in .qs
        if not value:
            return queryset

        start_date, end_date = get_fiscal_year_range(value)
        fiscal_year_filter = Q(contract__effective_date_from__gte=start_date) & Q(
            contract__effective_date_from__lte=end_date
        )
        return queryset.annotate(
            contracts_total=Sum("contract__amount_to_pay", filter=fiscal_year_filter),
            contracts_count=Count("contract", filter=fiscal_year_filter),
        )


class ServiceFilter(django_filters.FilterSet):
    id = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Service ID",
        queryset=Service.objects.all().only("id"),
        method="filter_services",
    )

    entity = django_filters.ModelMultipleChoiceFilter(
        help_text="Filter by Entity ID",
        queryset=Entity.objects.all(),
        method="filter_entity",
    )

    contractor = django_filters.ModelMultipleChoiceFilter(
        field_name="contractor",
        help_text="Filter by Contractor ID",
        queryset=Contractor.objects.all(),
        method="filter_contractor",
    )

    fiscal_year = django_filters.TypedChoiceFilter(
        choices=FISCAL_YEAR_CHOICES, coerce=int, method="filter_fiscal_year"
    )

    class Meta:
        model = Service
        fields = ["id", "entity", "group", "contractor", "fiscal_year"]

    def filter_services(self, queryset, name, value):
        if not value:
            return queryset

        entity_ids = [entity.id for entity in value]
        return queryset.filter(pk__in=entity_ids)

    def filter_entity(self, queryset, name, value):
        if not value:
            return queryset

        contracts = Contract.objects.filter(entity__in=value, parent=None)
        fiscal_year = self.form.cleaned_data.get("fiscal_year")

        if fiscal_year:
            start_date, end_date = get_fiscal_year_range(fiscal_year)
            contracts = contracts.filter(
                effective_date_from__gte=start_date, effective_date_from__lte=end_date
            )

        return queryset.filter(
            pk__in=[contract.entity_id for contract in contracts]
        ).distinct()

    def filter_contractor(self, queryset, name, value):
        if not value:
            return queryset

        contracts = Contract.objects.filter(contractors__in=value, parent=None)
        fiscal_year = self.form.cleaned_data.get("fiscal_year")

        if fiscal_year:
            start_date, end_date = get_fiscal_year_range(fiscal_year)
            contracts = contracts.filter(
                effective_date_from__gte=start_date, effective_date_from__lte=end_date
            )

        return queryset.filter(
            pk__in=[contract.service_id for contract in contracts]
        ).distinct()

    def filter_fiscal_year(self, queryset, name, value):
        return queryset
