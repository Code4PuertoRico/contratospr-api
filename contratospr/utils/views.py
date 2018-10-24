from django.db import DatabaseError, connections
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@never_cache
@require_safe
def liveness(request):
    return HttpResponse(status=200)


@never_cache
@require_safe
def readiness(request):
    try:
        connections["default"].introspection.table_names()
    except DatabaseError as e:
        status, reason = 503, str(e)
    else:
        status, reason = 200, None
    return HttpResponse(status=status, reason=reason)
