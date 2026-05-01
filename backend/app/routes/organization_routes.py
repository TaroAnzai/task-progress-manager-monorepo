from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import request, jsonify
from app.service_errors import format_error_response
from flask_login import login_required, current_user
from marshmallow import fields
from app.service_errors import ServiceError,ServiceValidationError
from app.decorators import with_common_error_responses
from app.services import organization_service
from app.schemas import (
    OrganizationSchema,
    OrganizationInputSchema,
    OrganizationUpdateSchema,
    OrganizationTreeSchema,
    MessageSchema,
    OrganizationQuerySchema,
    DeleteQuerySchema,
)

organization_bp = Blueprint("Organizations", __name__, url_prefix="/organizations", description="組織管理")

@organization_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code



def resolve_company_id(provided_company_id):
    if provided_company_id:
        return provided_company_id
    if not current_user or not current_user.organization:
        raise ServiceValidationError("company_id が指定されていないか、ユーザーに紐づく組織がありません。")
    return current_user.organization.company_id

@organization_bp.route("")
class OrganizationListResource(MethodView):
    @login_required
    @organization_bp.arguments(OrganizationInputSchema)
    @organization_bp.response(201, OrganizationSchema)
    @with_common_error_responses(organization_bp)
    def post(self, data):
        """組織作成"""
        resolved_company_id = resolve_company_id(data.get("company_id"))
        org = organization_service.create_organization(
            current_user,
            data.get("name"),
            data.get("org_code"),
            resolved_company_id,
            data.get("parent_id"),
        )
        return org

    @login_required
    @organization_bp.arguments(OrganizationQuerySchema, location="query")
    @organization_bp.response(200, OrganizationSchema(many=True))
    @with_common_error_responses(organization_bp)
    def get(self, args):
        """組織一覧取得(会社指定が無い場合は所属会社、または全組織)"""
        company_id = args.get("company_id")
        orgs =organization_service.get_organizations(current_user, company_id)
        return orgs


@organization_bp.route("/<int:org_id>")
class OrganizationResource(MethodView):
    @login_required
    @organization_bp.response(200, OrganizationSchema)
    @with_common_error_responses(organization_bp)
    def get(self, org_id):
        """組織取得"""
        org = organization_service.get_organization_by_id(org_id)
        return org

    @login_required
    @organization_bp.arguments(OrganizationUpdateSchema)
    @organization_bp.response(200, OrganizationSchema)
    @with_common_error_responses(organization_bp)
    def put(self, data, org_id):
        """組織更新"""
        org = organization_service.update_organization(
            current_user, org_id, data.get("name"), data.get("parent_id")
        )
        return org

    @login_required
    @organization_bp.arguments(DeleteQuerySchema, location="query")
    @organization_bp.response(200, MessageSchema)
    @with_common_error_responses(organization_bp)
    def delete(self, args, org_id):
        """組織削除"""
        force = args["force"] 
        success, message = organization_service.delete_organization(current_user, org_id, force)
        return {"message": message}

@organization_bp.route("/tree")
class OrganizationTreeResource(MethodView):
    @login_required
    @organization_bp.arguments(OrganizationQuerySchema, location="query")
    @organization_bp.response(200, OrganizationTreeSchema(many=True))
    @with_common_error_responses(organization_bp)
    def get(self,args):
        """組織ツリー取得(会社指定が無い場合は所属会社、または全組織)"""
        company_id = args.get("company_id")
        tree = organization_service.get_organization_tree(current_user, company_id)
        return tree

@organization_bp.route("<int:parent_id>/children")
class OrganizationChildrenResource(MethodView):
    @login_required
    @organization_bp.response(200, OrganizationSchema(many=True))
    @with_common_error_responses(organization_bp)
    def get(self,parent_id):
        """子組織取得"""
        children = organization_service.get_children(parent_id)
        return children

