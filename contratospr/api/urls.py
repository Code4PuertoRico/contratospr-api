from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view

from .views import HomePageView, TrendsGeneralView, TrendsServicesView
from .viewsets import (
    ContractorViewSet,
    ContractViewSet,
    DocumentViewSet,
    EntityViewSet,
    ServiceGroupViewSet,
    ServiceViewSet,
)

router = DefaultRouter()
api_root_view = router.get_api_root_view()
api_root_view.cls.__name__ = "Contratos de Puerto Rico"
api_root_view.cls.__doc__ = ""

router.register(r"contracts", ContractViewSet)
router.register(r"documents", DocumentViewSet)
router.register(r"contractors", ContractorViewSet)
router.register(r"entities", EntityViewSet)
router.register(r"service-groups", ServiceGroupViewSet)
router.register(r"services", ServiceViewSet)

urlpatterns = [
    path("v1/", include((router.urls, "api"), namespace="v1")),
    path("v1/pages/home/", HomePageView.as_view()),
    path("v1/pages/trends/general/", TrendsGeneralView.as_view()),
    path("v1/pages/trends/services/", TrendsServicesView.as_view()),
    path(
        "v1/docs/schema.json",
        get_schema_view(title="Contratos de Puerto Rico"),
        name="openapi-schema",
    ),
    path(
        "v1/docs/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
]
