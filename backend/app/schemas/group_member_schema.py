"""
GroupMember関連のスキーマ定義

- グループメンバーの追加・取得に使用
- OpenAPIに反映されるよう description / example を明示
"""

from marshmallow import Schema, fields, validate, ValidationError, validates_schema
from typing import Any


class GroupMemberReplaceSchema(Schema):
    """
    グループメンバー全置換スキーマ
    """

    user_ids = fields.List(
        fields.Int(),
        required=True,
        validate=validate.Length(min=1),
        metadata={
            "description": "グループに所属させるユーザーID一覧（1件以上必須）",
            "example": [1, 2, 3]
        }
    )

    @validates_schema
    def validate_members(self, data: dict[str, Any], **kwargs: Any) -> None:
        user_ids = data.get("user_ids", [])

        # 重複禁止
        if len(user_ids) != len(set(user_ids)):
            raise ValidationError(
                "user_ids must not contain duplicates",
                field_name="user_ids"
            )


class GroupMemberListResponseSchema(Schema):
    """
    グループメンバー一覧レスポンス
    """

    group_id = fields.Int(
        required=True,
        metadata={
            "description": "グループID",
            "example": 1
        }
    )

    user_ids = fields.List(
        fields.Int(),
        required=True,
        metadata={
            "description": "ユーザーID一覧",
            "example": [1, 2, 3]
        }
    )