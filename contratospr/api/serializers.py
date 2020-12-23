from django.core import serializers as django_serializers
from rest_framework import serializers

from ..contracts.models import (
    CollectionArtifact,
    CollectionJob,
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
)
from ..contracts.utils import get_current_fiscal_year

INITIAL_FISCAL_YEAR = 2016
CURRENT_FISCAL_YEAR = get_current_fiscal_year()
FISCAL_YEAR_CHOICES = [
    (year, str(year)) for year in range(INITIAL_FISCAL_YEAR, CURRENT_FISCAL_YEAR)
]


class RecursiveSerializer(serializers.Serializer):
    def to_native(self, value):
        return self.parent.to_native(value)


class HomeSerializer(serializers.Serializer):
    fiscal_year = serializers.ChoiceField(
        choices=FISCAL_YEAR_CHOICES, allow_null=False, initial=CURRENT_FISCAL_YEAR - 1
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
    contracts_total = serializers.DecimalField(
        max_digits=20, decimal_places=2, allow_null=True
    )

    contracts_count = serializers.IntegerField(allow_null=True)

    class Meta:
        model = ServiceGroup
        fields = [
            "id",
            "slug",
            "name",
            "contracts_count",
            "contracts_total",
            "created_at",
            "modified_at",
        ]


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


class BaseContractSerializer(serializers.ModelSerializer):
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


class ParentContractSerializer(BaseContractSerializer):
    pass


class ContractSerializer(BaseContractSerializer):
    parent = ParentContractSerializer()
    amendments = SimpleContractSerializer(many=True)


class CollectionArtifactContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        exclude = ["contractors"]


class CollectionArtifactEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = "__all__"


class CollectionArtifactServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class CollectionArtifactServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceGroup
        fields = "__all__"


class CollectionArtifactContractorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contractor
        fields = "__all__"


class CollectionArtifactDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"


class CollectionArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionArtifact
        fields = "__all__"

    def to_representation(self, instance):
        artifact_serializers = {
            "Contract": CollectionArtifactContractSerializer,
            "Entity": CollectionArtifactEntitySerializer,
            "Service": CollectionArtifactServiceSerializer,
            "ServiceGroup": CollectionArtifactServiceGroupSerializer,
            "Contractor": CollectionArtifactContractorSerializer,
            "Document": CollectionArtifactDocumentSerializer,
        }
        for deserialized_object in django_serializers.deserialize(
            "json", instance.serialized_data
        ):
            model = deserialized_object.object
            artifact_serializer = artifact_serializers.get(model._meta.object_name)

            if artifact_serializer:
                serializer = artifact_serializer(model)
                return {
                    "type": model._meta.model_name,
                    "created": instance.created,
                    "data": serializer.data,
                }

        return {}


class SimpleCollectionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionJob
        fields = [
            "id",
            "date_of_grant_start",
            "date_of_grant_end",
            "created_at",
            "modified_at",
        ]


class CollectionJobSerializer(serializers.ModelSerializer):
    artifacts = CollectionArtifactSerializer(many=True)

    class Meta:
        model = CollectionJob
        fields = [
            "id",
            "date_of_grant_start",
            "date_of_grant_end",
            "artifacts",
            "created_at",
            "modified_at",
        ]
