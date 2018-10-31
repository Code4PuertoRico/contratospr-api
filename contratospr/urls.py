from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .contracts.views import (
    contract,
    contractor,
    entity,
    filepreviews_webhook,
    index,
    search,
)
from .utils.views import liveness, readiness

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/filepreviews/", filepreviews_webhook),
    path("health/liveness/", liveness),
    path("health/readiness/", readiness),
    path("", index, name="index"),
    path("search/", search, name="search"),
    path("entities/<int:entity_id>/", entity, name="entity"),
    path("contracts/<int:contract_id>/", contract, name="contract"),
    path("contractors/<int:contractor_id>/", contractor, name="contractor"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
