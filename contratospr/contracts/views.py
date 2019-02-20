import datetime
import json
import statistics

from django import forms
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.util import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Contract, Contractor, Document, Entity, Service
from .search import search_contracts
from .tasks import detect_text
from .utils import get_chart_data, get_current_fiscal_year, get_fiscal_year_range

ITEMS_PER_PAGE = 20


class HomeForm(forms.Form):
    # TODO Don't hardcode choices
    fiscal_year = forms.TypedChoiceField(
        choices=[(2016, "2016"), (2017, "2017"), (2018, "2018"), (2019, "2019")],
        required=True,
        coerce=int,
        initial=get_current_fiscal_year() - 1,
    )


def index(request):
    form = HomeForm(request.POST) if request.method == "POST" else HomeForm()

    if form.is_valid():
        fiscal_year = form.cleaned_data.get("fiscal_year", get_current_fiscal_year())
    else:
        fiscal_year = get_current_fiscal_year()

    start_date, end_date = get_fiscal_year_range(fiscal_year)

    contracts = (
        Contract.objects.prefetch_related("contractors")
        .select_related("entity")
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
        .annotate(total=Sum("contract__amount_to_pay"))
        .filter(
            contract__parent=None,
            contract__effective_date_from__gte=start_date,
            contract__effective_date_from__lte=end_date,
        )
        .order_by("-total")
    )[:5]

    entities = (
        Entity.objects.prefetch_related("contract_set")
        .annotate(total=Sum("contract__amount_to_pay"))
        .filter(
            contract__parent=None,
            contract__effective_date_from__gte=start_date,
            contract__effective_date_from__lte=end_date,
        )
        .order_by("-total")
    )[:5]

    context = {
        "form": form,
        "recent_contracts": recent_contracts,
        "contractors": contractors,
        "entities": entities,
        "contracts_count": contracts.count(),
        "contracts_total": contracts_total,
    }

    return render(request, "contracts/index.html", context)


def entity(request, entity_slug):
    queryset = Entity.objects.prefetch_related("contract_set")

    entity = get_object_or_404(queryset, slug=entity_slug)

    contracts = (
        entity.contract_set.prefetch_related("contractors")
        .select_related("service")
        .order_by("-date_of_grant")
    )

    contracts_total = contracts.aggregate(total=Sum("amount_to_pay"))["total"]

    contractors = (
        Contractor.objects.filter(contract__in=[contract.pk for contract in contracts])
        .distinct()
        .order_by("name")
    )

    context = {
        "entity": entity,
        "contractors": contractors,
        "contracts": contracts,
        "contracts_total": contracts_total,
        "contracts_count": contracts.count(),
        "chart_data": get_chart_data(contracts),
    }

    return render(request, "contracts/entity.html", context)


def contract(request, contract_slug):
    queryset = Contract.objects.prefetch_related("contractors").select_related(
        "entity", "service", "parent", "parent"
    )
    contract = get_object_or_404(queryset, slug=contract_slug)
    contractors = contract.contractors.all().order_by("name")

    context = {"contract": contract, "contractors": contractors}

    return render(request, "contracts/contract.html", context)


def contractor(request, contractor_slug):
    queryset = Contractor.objects.prefetch_related(
        "contract_set", "contract_set__service", "contract_set__entity"
    )
    contractor = get_object_or_404(queryset, slug=contractor_slug)
    contracts = contractor.contract_set.filter(parent=None)
    contracts_total = contracts.aggregate(total=Sum("amount_to_pay"))["total"]
    services = Service.objects.filter(
        pk__in=[contract.service_id for contract in contracts]
    )
    entities = Entity.objects.filter(
        pk__in=[contract.entity_id for contract in contracts]
    )

    context = {
        "contractor": contractor,
        "contracts": contracts,
        "contracts_total": contracts_total,
        "contracts_count": contracts.count(),
        "entities": entities,
        "services": services,
        "chart_data": get_chart_data(contracts),
    }

    return render(request, "contracts/contractor.html", context)


def search(request):
    query = request.GET.get("q", "")
    service_id = request.GET.get("service")
    service_group_id = request.GET.get("service_group")
    page = request.GET.get("page", 1)
    contracts = search_contracts(
        query=query, service_id=service_id, service_group_id=service_group_id
    )
    paginator = Paginator(contracts, ITEMS_PER_PAGE)
    context = {"contracts": paginator.get_page(page), "query": query}
    return render(request, "contracts/search.html", context)


def entities(request):
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    entities = Entity.objects.prefetch_related("contract_set").all().order_by("name")

    if query:
        entities = entities.filter(name__icontains=query)

    paginator = Paginator(entities, ITEMS_PER_PAGE)
    context = {"entities": paginator.get_page(page), "query": query}
    return render(request, "contracts/entities.html", context)


def contractors(request):
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    contractors = (
        Contractor.objects.prefetch_related("contract_set").all().order_by("name")
    )

    if query:
        contractors = contractors.filter(name__icontains=query)

    paginator = Paginator(contractors, ITEMS_PER_PAGE)
    context = {"contractors": paginator.get_page(page), "query": query}
    return render(request, "contracts/contractors.html", context)


def get_trend(fiscal_year):
    start_date = timezone.make_aware(datetime.datetime(fiscal_year, 7, 1))
    end_date = timezone.make_aware(datetime.datetime(fiscal_year + 1, 6, 30))
    contracts = (
        Contract.objects.select_related("service", "service__group")
        .filter(effective_date_from__gte=start_date, effective_date_from__lte=end_date)
        .only("amount_to_pay", "service", "slug", "number")
    )

    contracts_count = len(contracts)
    contracts_total = 0
    contracts_average = 0
    contractors_count = 0
    contracts_median = 0
    min_amount_to_pay_contract = 0
    max_amount_to_pay_contract = 0

    if contracts_count:
        contracts_slug_amounts = []
        amounts_to_pay = []

        for contract in contracts:
            contracts_total += contract.amount_to_pay
            contracts_slug_amounts.append(
                {
                    "number": contract.number,
                    "slug": contract.slug,
                    "amount_to_pay": contract.amount_to_pay,
                }
            )
            amounts_to_pay.append(contract.amount_to_pay)

        contracts_slug_amounts.sort(key=lambda contract: contract["amount_to_pay"])
        min_amount_to_pay_contract = contracts_slug_amounts[0]
        max_amount_to_pay_contract = contracts_slug_amounts[-1]

        contracts_median = statistics.median(amounts_to_pay)
        contracts_average = contracts_total / contracts_count

        contractors_count = contracts.select_related("contractor").count()

    services_totals, services_group_totals = get_contract_types_totals(
        contracts, fiscal_year
    )

    context = {
        "fiscal_year": fiscal_year,
        "contratos": contracts,
        "data": {
            "general_data": {
                "contract_max_amount": max_amount_to_pay_contract,
                "contract_min_amount": min_amount_to_pay_contract,
                "totals": [
                    {
                        "title": "Total de Contratos",
                        "value": "{:,}".format(contracts_count),
                    },
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
            },
            "services_totals": {
                "title": "Totales por Tipos de Servicios",
                "total": len(services_totals),
                "value": services_totals,
            },
            "services_groups_totals": {
                "title": "Totales por Categoria de Servicios",
                "total": len(services_group_totals),
                "value": services_group_totals,
            },
        },
    }

    return context


def get_contract_types_totals(contracts, fiscal_year):
    service_totals = {}
    service_groups_totals = {}

    for contract in contracts:
        if contract.service.id in service_totals.keys():
            service_totals[contract.service.id]["total"] += contract.amount_to_pay
        else:
            service_totals[contract.service.id] = {
                "name": contract.service.name,
                "total": contract.amount_to_pay,
            }
        if contract.service.group.id in service_groups_totals.keys():
            service_groups_totals[contract.service.group.id][
                "total"
            ] += contract.amount_to_pay
        else:
            service_groups_totals[contract.service.group.id] = {
                "name": contract.service.group.name,
                "total": contract.amount_to_pay,
            }
    service_groups_totals = [
        {"id": key, "name": value["name"], "total": value["total"]}
        for key, value in service_groups_totals.items()
    ]
    service_totals = [
        {"id": key, "name": value["name"], "total": value["total"]}
        for key, value in service_totals.items()
    ]

    return service_totals, service_groups_totals


def trends(request):
    """
    Get interesting trends from the harvested data.
    """

    now = timezone.now()
    fiscal_year_end = timezone.make_aware(datetime.datetime(now.year, 6, 30))

    if now > fiscal_year_end:
        current_fiscal_year = now.year + 1
    else:
        current_fiscal_year = now.year

    fiscal_year = int(request.GET.get("fiscal_year", current_fiscal_year))

    context = {"a": get_trend(fiscal_year), "b": get_trend(fiscal_year - 1)}

    return render(request, "contracts/trends.html", context)


@csrf_exempt
def filepreviews_webhook(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf8"))
            document_id = body["user_data"]["document_id"]

            if document_id:
                pages = []

                original_file = body["original_file"] or {"metadata": {"ocr": []}}

                for result in original_file["metadata"]["ocr"]:
                    pages.append({"number": result["page"], "text": result["text"]})

                document = Document.objects.get(pk=document_id)
                document.update_preview_data(body)
                update_fields = ["preview_data_file"]

                if pages:
                    document.pages = pages
                    update_fields.append("pages")

                document.save(update_fields=update_fields)
                detect_text.send(document_id, force=not pages)
                return JsonResponse({"success": True}, status=200)

        except Exception:
            pass

    return JsonResponse({"success": False}, status=400)
