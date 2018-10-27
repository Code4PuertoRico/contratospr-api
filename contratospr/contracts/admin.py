from django.contrib import admin

from .models import Contract, Contractor, Document, Entity, Service


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "amendment",
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
    list_display = ["__str__", "created_at", "modified_at"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["source_id", "has_text", "created_at", "modified_at"]
    exclude = ["preview_data", "vision_data"]

    def has_text(self, obj):
        return len(obj.text) > 0

    has_text.boolean = True


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at", "modified_at"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at", "modified_at"]
