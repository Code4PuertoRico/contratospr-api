from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .contracts.views import filepreviews_webhook
from .utils.views import liveness, readiness

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/filepreviews/", filepreviews_webhook),
    path("health/liveness/", liveness),
    path("health/readiness/", readiness),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
