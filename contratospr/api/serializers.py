from rest_framework import serializers

from ..contracts.models import (
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)


class RecursiveSerializer(serializers.Serializer):
    def to_native(self, value):
        return self.parent.to_native(value)


class ContractorSerializer(serializers.ModelSerializer):
    contracts_total = serializers.DecimalField(
        max_digits=20, decimal_places=2, allow_null=True
    )
    contracts_count = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Contractor
        fields = [
            "id",
            "slug",
            "name",
            "source_id",
            "entity_id",
            "contracts_count",
            "contracts_total",
        ]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "source_id",
            "source_url",
            "file",
            "pages",
            "created_at",
            "modified_at",
        ]


class ServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceGroup
        fields = ["id", "name", "created_at", "modified_at"]


class ServiceSerializer(serializers.ModelSerializer):
    group = ServiceGroupSerializer()

    class Meta:
        model = Service
        fields = ["id", "name", "group", "created_at", "modified_at"]


class EntitySerializer(serializers.ModelSerializer):
    contracts_total = serializers.DecimalField(
        max_digits=20, decimal_places=2, allow_null=True
    )
    contracts_count = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Entity
        fields = [
            "id",
            "slug",
            "name",
            "source_id",
            "contracts_count",
            "contracts_total",
            "created_at",
            "modified_at",
        ]


class ContractSerializer(serializers.ModelSerializer):
    date_of_grant = serializers.DateTimeField(format="%Y-%m-%d")
    entity = EntitySerializer()
    service = ServiceSerializer()
    contractors = ContractorSerializer(many=True)
    document = serializers.HyperlinkedRelatedField(
        view_name="v1:document-detail", lookup_field="pk", read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id",
            "slug",
            "source_id",
            "number",
            "amendment",
            "date_of_grant",
            "effective_date_from",
            "effective_date_to",
            "cancellation_date",
            "amount_to_pay",
            "has_amendments",
            "exempt_id",
            "entity",
            "service",
            "document",
            "parent",
            "contractors",
            "created_at",
            "modified_at",
        ]

    def get_fields(self):
        fields = super(ContractSerializer, self).get_fields()
        fields["parent"] = ContractSerializer()
        return fields
