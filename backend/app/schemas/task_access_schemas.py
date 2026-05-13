from marshmallow import Schema, fields, validate
from app.constants import TaskAccessLevelEnum
from app.models import AccessSubjectType

class AuthorizedUserSchema(Schema):
    user_id = fields.Integer(dump_only=True, required=True, allow_none=False)
    name = fields.Str(dump_only=True, required=True, allow_none=False)

class AccessEntrySchema(Schema):
    subject_type = fields.Enum(AccessSubjectType,required=True,
        metadata={"description": "アクセス対象種別", "example": "USER"}
    )
    ref_id = fields.Int(required=True,
        metadata={"description": "対象ID","example": 10}
    )
    access_level = fields.Enum(TaskAccessLevelEnum,required=True,
        metadata={"description": "アクセスレベル", "example": "EDIT"}
    )


class AccessLevelInputSchema(Schema):
    accesses = fields.List(fields.Nested(AccessEntrySchema), required=True,
                            metadata={"description": "アクセス設定一覧"}
    )

class TaskAccessResponseSchema(Schema):
    id = fields.Int(required=True, metadata={
            "description": "TaskAccess ID", "example": 1,},
    )
    subject_id = fields.Int(required=True, metadata={
            "description": "AccessSubject ID", "example": 10,},
    )
    subject_type = fields.Enum(AccessSubjectType, required=True, metadata={
            "description": "アクセス対象種別", "example": "USER",},
    )
    ref_id = fields.Int(required=True, metadata={
            "description": "対象ID。USERならuser_id、ORGANIZATIONならorganization_id、GROUPならgroup_id",
            "example": 3,
        },
    )
    access_level = fields.Enum(TaskAccessLevelEnum, required=True, metadata={
            "description": "アクセスレベル", "example": "EDIT",},
    )
    display_name = fields.Str(allow_none=True, metadata={
            "description": "画面表示用の名称。USERならユーザー名、ORGANIZATIONなら組織名、GROUPならグループ名",
            "example": "営業チームA",
        },
    )


class TaskAccessListResponseSchema(Schema):
    accesses = fields.List(
        fields.Nested(TaskAccessResponseSchema),
        required=True,
        metadata={
            "description": "タスクに設定されているアクセス一覧",
        },
    )


# For serch scope

class AccessSubjectSearchQuerySchema(Schema):
    keyword = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={
            "description": "検索キーワード",
            "example": "営業",
        },
    )

    subject_type = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["USER", "ORGANIZATION", "GROUP"]),
        metadata={
            "description": "検索対象種別。未指定の場合は全種別を検索する",
            "example": "USER",
        },
    )

    limit = fields.Integer(
        required=False,
        load_default=20,
        validate=validate.Range(min=1, max=50),
        metadata={
            "description": "最大取得件数",
            "example": 20,
        },
    )


class AccessSubjectSearchItemSchema(Schema):
    subject_type = fields.String(
        required=True,
        validate=validate.OneOf(["USER", "ORGANIZATION", "GROUP"]),
        metadata={
            "description": "アクセス対象種別",
            "example": "USER",
        },
    )

    ref_id = fields.Integer(
        required=True,
        metadata={
            "description": "対象データのID。USERならUser.id、ORGANIZATIONならOrganization.id、GROUPならGroup.id",
            "example": 1,
        },
    )

    display_name = fields.String(
        required=True,
        metadata={
            "description": "画面表示名",
            "example": "山田太郎",
        },
    )

    description = fields.String(
        required=False,
        allow_none=True,
        metadata={
            "description": "補足情報。メールアドレス、組織コード、グループ種別など",
            "example": "yamada@example.com",
        },
    )


class AccessSubjectSearchResponseSchema(Schema):
    subjects = fields.List(
        fields.Nested(AccessSubjectSearchItemSchema),
        required=True,
    )
