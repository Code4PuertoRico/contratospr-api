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
                Document.objects.filter(pk=document_id).update(preview_data=body)
                detect_text.send(document_id)
                return JsonResponse({"success": True}, status=200)

        except Exception:
            pass

    return JsonResponse({"success": False}, status=400)
