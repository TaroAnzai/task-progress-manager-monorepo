import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Company, Organization
from app.service_errors import ServiceNotFoundError, ServiceValidationError
from app.services import company_service as service


def test_company_not_found_paths():
    for call in (service.get_all_companies, lambda: service.get_company_by_id(999999),
                 lambda: service.get_company_by_id_with_deleted(999999)):
        with pytest.raises(ServiceNotFoundError): call()


def test_company_duplicate_and_permanent_delete_relation(test_company, root_org):
    with pytest.raises(ServiceValidationError, match="already exists"):
        service.create_company(test_company["name"])
    with pytest.raises(ServiceValidationError, match="related organizations"):
        service.delete_company_permanently(test_company["id"])


@pytest.mark.parametrize("operation", ["create", "update", "permanent_delete"])
def test_company_database_errors_rollback(monkeypatch, operation):
    company = Company(name=f"DB error {operation}")
    db.session.add(company); db.session.flush()
    if operation == "create":
        company.name = "existing placeholder"
        db.session.flush()
    monkeypatch.setattr(db.session, "commit", lambda: (_ for _ in ()).throw(IntegrityError("x", {}, None)))
    with pytest.raises(ServiceValidationError):
        if operation == "create": service.create_company("new db-error company")
        elif operation == "update": service.update_company(company.id, "updated")
        else: service.delete_company_permanently(company.id)
