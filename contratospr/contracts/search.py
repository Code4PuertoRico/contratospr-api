import types

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import (
    Date,
    Document,
    InnerDoc,
    Keyword,
    Nested,
    Object,
    Q,
    ScaledFloat,
    Search,
    Text,
    analyzer,
)

client = Elasticsearch([settings.ELASTICSEARCH_URL])

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["standard", "lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)


class ContractDocumentPage(InnerDoc):
    text = Text(analyzer=html_strip)


class Contractor(InnerDoc):
    name = Text()


class Entity(InnerDoc):
    name = Keyword()


class Contract(Document):
    number = Text()
    entity = Object(Entity)
    document = Nested(ContractDocumentPage)
    contractors = Nested(Contractor)
    date_of_grant = Date()
    effective_date_to = Date()
    effective_date_from = Date()
    amount_to_pay = ScaledFloat(scaling_factor=100)

    class Index:
        name = "contracts"


def init():
    Contract.init(using=client)


def index_contract(obj):
    def _index_contract(obj, persist=True):
        contract = Contract(
            _id=obj.pk,
            number=obj.number,
            date_of_grant=obj.date_of_grant,
            effective_date_from=obj.effective_date_from,
            effective_date_to=obj.effective_date_to,
            amount_to_pay=obj.amount_to_pay,
        )

        if obj.entity_id:
            contract.entity = Entity(_id=obj.entity_id, name=obj.entity.name)

        if obj.document_id and obj.document.pages:
            for page in obj.document.pages:
                contract.document.append(ContractDocumentPage(text=page["text"]))

        for contractor in obj.contractors.all():
            contract.contractors.append(Contractor(name=contractor.name))

        if persist:
            return contract.save(using=client)

        return contract

    def _generate_bulk_data(contracts):
        for contract in contracts:
            doc = _index_contract(contract, persist=False)
            yield doc.to_dict(include_meta=True)

    if isinstance(obj, types.GeneratorType):
        return streaming_bulk(client, _generate_bulk_data(obj))

    return _index_contract(obj, persist=True)


def search_contracts(query):
    s = Search(using=client).query(
        Q(
            "nested",
            path="contractors",
            query=Q("match", contractors__name=query),
            inner_hits={"highlight": {"fields": {"contractors.name": {}}}},
        )
        | Q(
            "nested",
            path="document",
            query=Q("match", document__text=query),
            inner_hits={"highlight": {"fields": {"document.text": {}}}},
        )
    )

    return s.execute()
