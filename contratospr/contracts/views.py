import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Document
from .tasks import detect_text


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
                detect_text.delay(document_id, force=not pages)
                return JsonResponse({"success": True}, status=200)

        except Exception:
            pass

    return JsonResponse({"success": False}, status=400)
