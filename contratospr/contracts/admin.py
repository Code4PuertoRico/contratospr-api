from django.contrib import admin

from .models import Contract, Contractor, Document, Entity, Service


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "amendment",
        "source_id",
        "date_of_grant",
        "service",
        "has_document",
        "created_at",
        "modified_at",
    ]

    search_fields = ["source_id", "number"]

    actions = ["request_document"]

    def has_document(self, obj):
        return bool(obj.document_id)

    has_document.boolean = True

    def request_document(self, request, queryset):
        from .tasks import request_contract_document

        for contract in queryset:
            if not contract.document_id:
                request_contract_document.send(contract.source_id)

    request_document.short_description = "Request document for selected contracts"


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ["name", "source_id", "created_at", "modified_at"]
    search_fields = ["name", "source_id"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["source_id", "has_text", "created_at", "modified_at"]
    exclude = ["pages"]
    search_fields = ["source_id"]
    actions = ["detect_text"]

    def has_text(self, obj):
        return bool(obj.pages)

    has_text.boolean = True

    def detect_text(self, request, queryset):
        from .tasks import detect_text

        for document in queryset:
            if not document.vision_data:
                detect_text.send(document.pk, force=True)

    detect_text.short_description = (
        "Detect text using Vision API for selected documents"
    )


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["name", "source_id", "created_at", "modified_at"]
    search_fields = ["name", "source_id"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "created_at", "modified_at"]
    search_fields = ["name", "group"]
