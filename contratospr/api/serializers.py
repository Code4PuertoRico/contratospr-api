from rest_framework import serializers

from ..contracts.models import (
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from ..contracts.utils import get_current_fiscal_year


class RecursiveSerializer(serializers.Serializer):
    def to_native(self, value):
        return self.parent.to_native(value)


class HomeSerializer(serializers.Serializer):
    fiscal_year = serializers.ChoiceField(
        choices=[(2016, "2016"), (2017, "2017"), (2018, "2018"), (2019, "2019")],
        allow_null=False,
        initial=get_current_fiscal_year() - 1,
    )


class ContractorSerializer(serializers.ModelSerializer):
    contracts_total = serializers.DecimalField(
        max_digits=20, decimal_places=2, allow_null=True
    )
    contracts_count = serializers.IntegerField(allow_null=True)

    entities = serializers.SerializerMethodField()

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
            "entities",
        ]

    def get_entities(self, obj):
        contracts = obj.contract_set.all().only("id")
        entities = Entity.objects.filter(contract__in=contracts).distinct()
        return EntitySerializer(entities, many=True).data


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
        fields = ["id", "slug", "name", "created_at", "modified_at"]


class ServiceSerializer(serializers.ModelSerializer):
    group = ServiceGroupSerializer()

    contracts_total = serializers.DecimalField(
        max_digits=20, decimal_places=2, allow_null=True
    )

    contracts_count = serializers.IntegerField(allow_null=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "slug",
            "name",
            "group",
            "contracts_count",
            "contracts_total",
            "created_at",
            "modified_at",
        ]


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
            "contracts_total",
            "contracts_count",
            "created_at",
            "modified_at",
        ]


class SimpleContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            "id",
            "slug",
            "source_id",
            "number",
            "amendment",
            "amount_to_pay",
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
            "amendments",
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
        fields["amendments"] = SimpleContractSerializer(many=True)
        return fields
