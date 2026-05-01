
from sqlalchemy import exists, select, text
from sqlalchemy.exc import IntegrityError
from app.models import Organization, db, Company
from app.service_errors import (
    ServiceValidationError,
    ServiceAuthenticationError,
    ServicePermissionError,
    ServiceNotFoundError,
)

# Create
def create_company(name: str):
    # 論理削除されていないデータとのみ重複チェック
    existing = Company.query.filter_by(name=name, is_deleted=False).first()
    if existing:
        raise ServiceValidationError("Company with the same name already exists.")

    company = Company(name=name)
    db.session.add(company)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ServiceValidationError("Failed to create company due to DB constraint.")

    return company


# Read: 全件取得（論理削除除く）
def get_all_companies():
    #companies = Company.query.filter_by(is_deleted=False).all()
    companies = Company.query.all()
    if not companies:
        raise ServiceNotFoundError("Companies not found")
    return companies


# Read: IDで取得（論理削除除く）
def get_company_by_id(company_id):
    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        raise ServiceNotFoundError("Company not found")
    return company


# Read: 削除済も含めて取得
def get_company_by_id_with_deleted(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        raise ServiceNotFoundError("Company not found")
    return company


# Update
def update_company(company_id, new_name):
    company = get_company_by_id(company_id)
    if not company:
        raise ServiceNotFoundError("Company not found")
    company.name = new_name
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ServiceValidationError("Failed to update company name due to DB constraint.")

    return company


# 論理削除
def delete_company(company_id):
    company = get_company_by_id(company_id)
    if not company:
        raise ServiceNotFoundError("Company not found")

    company.soft_delete()
    db.session.commit()
    return True


# 論理削除から復元
def restore_company(company_id: int):
    company = get_company_by_id_with_deleted(company_id)
    if not company:
        raise ServiceNotFoundError("Company not found")

    # 同じ名前で論理削除されていない別レコードが存在する場合、復元禁止
    duplicate = Company.query.filter(
        Company.name == company.name,
        Company.is_deleted == False,
        Company.id != company.id
    ).first()
    if duplicate:
        raise ServiceValidationError("Cannot restore company: same name already exists.")

    company.restore()
    db.session.commit()
    return True





# （任意）物理削除
def delete_company_permanently(company_id):
    company = get_company_by_id_with_deleted(company_id)
    if not company:
        raise ServiceNotFoundError("Company not found")
    stmt = select(exists().where(Organization.company_id == company_id))
    has_organization = db.session.execute(stmt).scalar()
    if has_organization:
        raise ServiceValidationError("Cannot delete company because it has related organizations.")
    try:
        db.session.delete(company)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        raise ServiceValidationError(f"Cannot delete company due to foreign key constraint.{e}")
    return True
