import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import Contract, Contractor, Document, Entity
from .search import search_contracts
from .tasks import detect_text


def index(request):
    entities = Entity.objects.all()
    context = {"entities": entities}
    return render(request, "contracts/entities.html", context)


def entity(request, entity_id):
    entity = get_object_or_404(Entity, pk=entity_id)
    context = {"entity": entity}
    return render(request, "contracts/entity.html", context)


def contract(request, contract_id):
    queryset = Contract.objects.select_related("entity")
    contract = get_object_or_404(queryset, pk=contract_id)
    context = {"contract": contract}
    return render(request, "contracts/contract.html", context)


def contractor(request, contractor_id):
    contractor = get_object_or_404(Contractor, pk=contractor_id)
    context = {"contractor": contractor}
    return render(request, "contracts/contractor.html", context)


def search(request):
    query = request.GET.get("q")
    page = request.GET.get("page", 1)
    contracts = search_contracts(query=query) if query else []
    paginator = Paginator(contracts, 12)
    context = {"contracts": paginator.get_page(page)}
    return render(request, "contracts/search.html", context)


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
