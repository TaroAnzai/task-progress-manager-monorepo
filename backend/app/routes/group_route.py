from typing import Any, cast

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_login import current_user
from sqlalchemy.orm import Session
from app.extensions import db
from app.schemas.group_schema import (
    GroupCreateSchema,
    GroupUpdateSchema,
    GroupResponseSchema,
)
from app.services.group_service import (
    create_group,
    get_group,
    update_group,
    delete_group,
    list_groups,
)
from app.service_errors import ServiceError, format_error_response
from backend.app.models import User

group_bp = Blueprint("groups", __name__, url_prefix="/groups", description="Group API")
@group_bp.errorhandler(ServiceError)
def handle_service_error(e: ServiceError):
    return jsonify(format_error_response(e.code, e.name, e.description)), e.code

# =====================
# 一覧 / 作成
# =====================
@group_bp.route("")
class GroupListResource(MethodView):

    @group_bp.response(200, GroupResponseSchema(many=True))
    def get(self):
        """グループ一覧取得"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        return list_groups(session, user)

    @group_bp.arguments(GroupCreateSchema)
    @group_bp.response(201, GroupResponseSchema)
    def post(self, data:dict[str, Any]):
        """グループ作成"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        return create_group(session, data, user)


# =====================
# 個別操作
# =====================
@group_bp.route("/<int:group_id>")
class GroupResource(MethodView):

    @group_bp.response(200, GroupResponseSchema)
    def get(self, group_id:int):
        """グループ取得"""
        session = cast(Session, db.session)
        return get_group(session, group_id)

    @group_bp.arguments(GroupUpdateSchema)
    @group_bp.response(200, GroupResponseSchema)
    def patch(self, data:dict[str, Any], group_id:int):
        """グループ更新"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        return update_group(session, group_id, data, user)

    @group_bp.response(204)
    def delete(self, group_id:int):
        """グループ削除"""
        session = cast(Session, db.session)
        user = cast(User, current_user)
        delete_group(session, group_id, user)
        return None