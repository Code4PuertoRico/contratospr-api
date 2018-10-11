import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Document


@csrf_exempt
def filepreviews_webhook(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf8"))
            user_data = body.get("user_data", {})
            document_id = user_data.get("document_id")
            Document.objects.filter(pk=document_id).update(preview_data=body)
            return JsonResponse({"success": True}, status=200)
        except Exception:
            pass

    return JsonResponse({"success": False}, status=400)
