import json

from django import forms
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
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
