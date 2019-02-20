import debug_toolbar
from django.contrib import admin
from django.urls import include, path

from .api import urls as api_urls
from .contracts.views import (
    contract,
    contractor,
    contractors,
    entities,
    entity,
    filepreviews_webhook,
    index,
    search,
    trends,
)
from .utils.views import liveness, readiness

urlpatterns = [
    path("__debug__/", include(debug_toolbar.urls)),
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
    path("api/webhooks/filepreviews/", filepreviews_webhook),
    path("health/liveness/", liveness),
    path("health/readiness/", readiness),
    path("", index, name="index"),
    path("buscar/", search, name="search"),
    path("entidades/", entities, name="entities"),
    path("entidades/<slug:entity_slug>/", entity, name="entity"),
    path("contratos/<slug:contract_slug>/", contract, name="contract"),
    path("contratistas/", contractors, name="contractors"),
    path("contratistas/<slug:contractor_slug>/", contractor, name="contractor"),
    path("trends/", trends, name="trends"),
]
