from typing import Any, cast
from flask import jsonify
from sqlalchemy.orm import Session
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_login import current_user
from app.extensions import db
from app.schemas.group_member_schema import (
    GroupMemberReplaceSchema,
    GroupMemberListResponseSchema,
)
from app.services.group_member_service import (
    get_group_members,
    replace_group_members,
)
from app.models import User
from app.service_errors import ServiceError, format_error_response

group_member_bp = Blueprint(
    "group_members",
    __name__,
    url_prefix="/groups/<int:group_id>/members",
    description="Group Member API"
)
@group_member_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code

# =====================
# メンバー一覧
# =====================
@group_member_bp.route("")
class GroupMemberResource(MethodView):

    @group_member_bp.response(200, GroupMemberListResponseSchema)
    def get(self, group_id:int):
        """グループメンバー一覧取得"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        return get_group_members(session, group_id, user)

    @group_member_bp.arguments(GroupMemberReplaceSchema)
    @group_member_bp.response(200, GroupMemberListResponseSchema)
    def put(self, data:dict[str,Any], group_id:int):
        """グループメンバー全置換"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        return replace_group_members(session, group_id, data["user_ids"], user)