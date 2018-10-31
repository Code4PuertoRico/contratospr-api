from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Document, InnerDoc, Nested, Object, Q, Search, Text

client = Elasticsearch([settings.ELASTICSEARCH_URL])


class ContractDocumentPage(InnerDoc):
    text = Text()


class ContractDocument(InnerDoc):
    pages = Nested(ContractDocumentPage)


class Contractor(InnerDoc):
    name = Text()


class Contract(Document):
    number = Text()
    document = Object(ContractDocument)
    contractors = Nested(Contractor)

    class Index:
        name = "contracts"


def init():
    Contract.init(using=client)


def index_contract(obj):
    contract = Contract(_id=obj.pk, number=obj.number)

    if obj.document:
        pages = []
        for page in obj.document.pages:
            pages.append(ContractDocumentPage(text=page["text"]))

        if pages:
            contract.document = ContractDocument(pages=pages)

    for contractor in obj.contractors.all():
        contract.contractors.append(Contractor(name=contractor.name))

    contract.save(using=client)


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
            path="document.pages",
            query=Q("match", document__pages__text=query),
            inner_hits={"highlight": {"fields": {"document.pages.text": {}}}},
        )
    )

    return s.execute()
