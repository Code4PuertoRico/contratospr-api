import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .api import urls as api_urls
from .utils.views import liveness, readiness

urlpatterns = [
    path("__debug__/", include(debug_toolbar.urls)),
    path("admin/", admin.site.urls),
    path("health/liveness/", liveness),
    path("health/readiness/", readiness),
    path("", include(api_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
