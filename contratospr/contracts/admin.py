from django.contrib import admin
from django.db.models import Q

from .models import (
    CollectionArtifact,
    CollectionJob,
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)


class DocumentFileListFilter(admin.SimpleListFilter):
    title = "Has file"
    parameter_name = "has_file"

    def lookups(self, request, model_admin):
        return (("yes", "Yes"), ("no", "No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(file__isnull=False).exclude(file="")
        elif self.value() == "no":
            return queryset.filter(Q(file__isnull=True) | Q(file=""))
        return queryset


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "amendment",
        "slug",
        "source_id",
        "date_of_grant",
        "service",
        "has_document",
        "created_at",
        "modified_at",
    ]

    search_fields = ["source_id", "number"]
    exclude = ["search_vector"]
    actions = ["request_document"]
    raw_id_fields = ["entity", "service", "document", "contractors", "parent"]

    def has_document(self, obj):
        return bool(obj.document_id)

    has_document.boolean = True

    def request_document(self, request, queryset):
        from .tasks import request_contract_document

        for contract in queryset:
            if not contract.document_id:
                request_contract_document.delay(contract.source_id)

    request_document.short_description = "Request document for selected contracts"


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "source_id", "created_at", "modified_at"]
    search_fields = ["name", "source_id"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["source_id", "file", "has_text", "created_at", "modified_at"]
    exclude = ["pages"]
    search_fields = ["source_id"]
    actions = ["download_source", "detect_text"]
    list_filter = [DocumentFileListFilter]

    def has_text(self, obj):
        return bool(obj.pages)

    has_text.boolean = True

    def download_source(self, request, queryset):
        from .tasks import download_document

        for document in queryset:
            download_document.delay(document.pk)

    download_source.short_description = "Download source file"

    def detect_text(self, request, queryset):
        from .tasks import detect_text

        for document in queryset:
            detect_text.delay(document.pk)

    detect_text.short_description = "Detect text for selected documents"


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "source_id", "created_at", "modified_at"]
    search_fields = ["name", "source_id"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "group", "created_at", "modified_at"]
    search_fields = ["name", "group__name"]


@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at", "modified_at"]
    search_fields = ["name"]


@admin.register(CollectionJob)
class CollectionJobAdmin(admin.ModelAdmin):
    pass


@admin.register(CollectionArtifact)
class CollectionArtifactAdmin(admin.ModelAdmin):
    list_display = ["object_repr", "collection_job", "created"]
