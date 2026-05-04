"""
Group関連のスキーマ定義

- グループの作成・更新・取得に使用
- OpenAPIに反映されるように description / example を明示
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from typing import Any

from app.models import GroupScopeType


# =====================
# Group 作成
# =====================
class GroupCreateSchema(Schema):
    """
    グループ作成用スキーマ
    """

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        metadata={
            "description": "グループ名",
            "example": "営業チームA"
        }
    )

    scope_type = fields.Enum(
        GroupScopeType,
        required=True,
        metadata={
            "description": "公開範囲（PRIVATE / ORGANIZATION / GLOBAL）",
            "example": "ORGANIZATION"
        }
    )

    organization_id = fields.Int(
        required=False,
        allow_none=True,
        metadata={
            "description": "組織ID（scope_typeがORGANIZATIONの場合のみ必須）",
            "example": 10
        }
    )
    member_user_ids = fields.List(
        fields.Int(),
        required=True,
        metadata={
            "description": "メンバーのユーザーIDリスト",
            "example": [1, 2, 3]
        }
    )

    @validates_schema
    def validate_scope(self, data:dict[str, Any], **kwargs:Any) -> None:
        """
        scope_typeに応じたバリデーション
        """
        scope = data.get("scope_type")
        org_id = data.get("organization_id")

        if scope == GroupScopeType.ORGANIZATION:
            if not org_id:
                raise ValidationError(
                    "organization_id is required when scope_type is ORGANIZATION",
                    field_name="organization_id"
                )
        else:
            # PRIVATE / GLOBAL の場合は organization_id を使わない
            data["organization_id"] = None

# =====================
# Group 更新
# =====================
class GroupUpdateSchema(Schema):
    """
    グループ更新用スキーマ
    """

    name = fields.Str(
        required=False,
        validate=validate.Length(min=1, max=255),
        metadata={
            "description": "グループ名",
            "example": "営業チームB"
        }
    )

    scope_type = fields.Enum(
        GroupScopeType,
        required=False,
        metadata={
            "description": "公開範囲（PRIVATE / ORGANIZATION / GLOBAL）",
            "example": "ORGANIZATION"
        }
    )

    organization_id = fields.Int(
        required=False,
        allow_none=True,
        metadata={
            "description": "組織ID",
            "example": 10
        }
    )

    @validates_schema
    def validate_scope(self, data: dict[str, Any], **kwargs: Any) -> None:
        scope = data.get("scope_type")
        org_id = data.get("organization_id")

        # scope_typeが指定された場合のみチェック
        if scope == GroupScopeType.ORGANIZATION:
            if not org_id:
                raise ValidationError(
                    "organization_id is required when scope_type is ORGANIZATION",
                    field_name="organization_id"
                )
# =====================
# Group レスポンス
# =====================
class GroupResponseSchema(Schema):
    """
    グループ情報レスポンス
    """

    id = fields.Int(
        required=True,
        metadata={
            "description": "グループID",
            "example": 1
        }
    )

    name = fields.Str(
        required=True,
        metadata={
            "description": "グループ名",
            "example": "営業チームA"
        }
    )

    scope_type = fields.Enum(
        GroupScopeType,
        required=True,
        metadata={
            "description": "公開範囲",
            "example": "ORGANIZATION",
        }
    )

    organization_id = fields.Int(
        allow_none=True,
        metadata={
            "description": "組織ID",
            "example": 10
        }
    )

    owner_user_id = fields.Int(
        required=True,
        metadata={
            "description": "作成ユーザーID",
            "example": 5
        }
    )