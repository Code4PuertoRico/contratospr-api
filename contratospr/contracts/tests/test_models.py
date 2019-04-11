import pytest

from ..models import (
    Contract,
    Contractor,
    Document,
    Entity,
    Service,
    ServiceGroup,
    document_file_path,
)


@pytest.fixture
def get_entity():
    """Returns an Entity factory with defaults: name='Test Entity'"""

    def _get_entity(name="Test Entity"):
        entity_instance = Entity(name=name)
        return entity_instance

    return _get_entity


@pytest.fixture
def get_service_group():
    """Returns a ServiceGroup factory with defaults: name='Test Service Group'"""

    def _get_service_group(name="Test Service Group"):
        service_group_instance = ServiceGroup(name=name)
        return service_group_instance

    return _get_service_group


@pytest.fixture
def get_service(get_service_group):
    """Returns a Service factory with defaults: name='Test Service'"""

    def _get_service(name="Test Service", group=1):
        service_group = get_service_group(group)
        service_instance = Service(name=name, group=service_group)
        return service_instance

    return _get_service


@pytest.fixture
def get_document():
    """Returns a Document factory with defaults: file='test.txt', source_id=1"""

    def _get_document(file="test.txt", source_id=1):
        document_instance = Document(file=file, source_id=source_id)
        return document_instance

    return _get_document


@pytest.fixture
def get_contractor():
    """Returns a Contractor factory with defaults: name='Test Contractor', source_id=1, entity_id=1"""

    def _get_contractor(name="Test Contractor", source_id=1, entity_id=1):
        contractor_instance = Contractor(
            name=name, source_id=source_id, entity_id=entity_id
        )
        return contractor_instance

    return _get_contractor


@pytest.fixture
def get_contract(get_entity):
    """Returns a Contract factory with defaults: entity=1, source_id=1, number=T1"""

    def _get_contract(entity=None, source_id=1, number="T1"):
        if not entity:
            entity = get_entity()
        contract_instance = Contract(entity=entity, source_id=source_id, number=number)
        return contract_instance

    return _get_contract


class TestModelHelpers:
    def test_document_file_path(self, tmpdir, get_document):
        document = get_document()
        filename = "document"
        assert (
            document_file_path(document, filename)
            == f"documents/{document.source_id}/{filename}"
        )


class TestEntity:
    def test_instance_str(self, get_entity):
        entity = get_entity()
        assert str(entity) == "Test Entity"


class TestServiceGroup:
    def test_instance_str(self, get_service_group):
        service_group = get_service_group()
        assert str(service_group) == "Test Service Group"


class TestService:
    def test_instance_str(self, get_service):
        service = get_service()
        assert str(service) == "Test Service"


class TestDocument:
    def test_instance_str(self, get_document):
        document = get_document()
        assert str(document) == "1"


class TestContractor:
    def test_instance_str(self, get_contractor):
        contractor = get_contractor()
        assert str(contractor) == "Test Contractor"


@pytest.mark.django_db
class TestContract:
    def test_instance_str(self, get_contract):
        contract = get_contract()
        assert str(contract) == "T1"
