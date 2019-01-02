import datetime
import json
import statistics
from collections import defaultdict

from django import forms
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Contract, Contractor, Document, Entity, Service
from .search import search_contracts
from .tasks import detect_text

ITEMS_PER_PAGE = 20


class HomeForm(forms.Form):
    dias = forms.TypedChoiceField(
        choices=[(30, "30 días"), (60, "60 días"), (90, "90 días"), (120, "120 días")],
        required=True,
        coerce=int,
        initial=90,
    )


def get_chart_data(contracts):
    chart_data = []
    chart_data_groups = defaultdict(list)

    for contract in contracts:
        chart_data_groups[contract.date_of_grant.date()].append(contract.amount_to_pay)

    for date_of_grant, amounts in chart_data_groups.items():
        chart_data.append(
            {"x": date_of_grant, "y": sum(amounts), "contracts": len(amounts)}
        )

    return chart_data


def index(request):
    now = timezone.now()
    form = HomeForm(request.POST) if request.method == "POST" else HomeForm()

    if form.is_valid():
        last_x_days = now - datetime.timedelta(days=form.cleaned_data["dias"])
    else:
        last_x_days = now - datetime.timedelta(days=90)

    contracts = (
        Contract.objects.prefetch_related("contractors")
        .select_related("entity")
        .filter(parent=None, date_of_grant__lte=now, date_of_grant__gte=last_x_days)
    )
    contracts_total = contracts.aggregate(total=Sum("amount_to_pay"))["total"]

    recent_contracts = contracts.order_by("-date_of_grant")[:5]

    contractors = (
        Contractor.objects.prefetch_related("contract_set")
        .annotate(total=Sum("contract__amount_to_pay"))
        .filter(
            contract__parent=None,
            contract__date_of_grant__lte=now,
            contract__date_of_grant__gte=last_x_days,
        )
        .order_by("-total")
    )[:5]

    entities = (
        Entity.objects.prefetch_related("contract_set")
        .annotate(total=Sum("contract__amount_to_pay"))
        .filter(
            contract__parent=None,
            contract__date_of_grant__lte=now,
            contract__date_of_grant__gte=last_x_days,
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
    page = request.GET.get("page", 1)
    contracts = search_contracts(query=query, service_id=service_id)
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
    contracts = Contract.objects.filter(
        effective_date_from__gte=start_date, effective_date_from__lte=end_date
    ).only("amount_to_pay", "service_id", "slug", "number")

    contracts_count = len(contracts)
    contracts_total = 0
    contracts_average = 0
    contractors_count = 0
    contracts_median = 0
    min_amount_to_pay_contract = 0
    max_amount_to_pay_contract = 0

    if contracts_count:
        contracts_slug_amounts = [
            {
                "number": contract.number,
                "slug": contract.slug,
                "amount_to_pay": contract.amount_to_pay,
            }
            for contract in contracts
        ]
        contracts_slug_amounts.sort(key=lambda contract: contract["amount_to_pay"])
        min_amount_to_pay_contract = contracts_slug_amounts[0]
        max_amount_to_pay_contract = contracts_slug_amounts[-1]

        amounts_to_pay = [
            contract["amount_to_pay"] for contract in contracts_slug_amounts
        ]
        contracts_total = sum(amounts_to_pay)
        contracts_median = statistics.median(amounts_to_pay)
        contracts_average = contracts_total / contracts_count

        contractors_count = Contractor.objects.filter(contract__in=contracts).count()

    services_below_median, services_above_median = get_contract_types(
        contracts, contracts_median
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
            "services": [
                {
                    "title": "Servicios Por Debajo de la Media",
                    "value": services_below_median,
                },
                {
                    "title": "Servicios Sobre de la Media",
                    "value": services_above_median,
                },
            ],
        },
    }

    return context


def get_contract_types(contracts, contracts_median):
    service_ids_below_median = []
    service_ids_above_median = []

    for contract in contracts:
        if contract.amount_to_pay < contracts_median:
            service_ids_below_median.append(contract.service_id)
        else:
            service_ids_above_median.append(contract.service_id)

    services_below_median = Service.objects.filter(pk__in=set(service_ids_below_median))

    services_above_median = Service.objects.filter(pk__in=set(service_ids_above_median))

    return services_below_median, services_above_median


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
