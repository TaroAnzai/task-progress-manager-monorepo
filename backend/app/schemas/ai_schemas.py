from marshmallow import Schema, fields,validate
import enum

class AISuggestionMode(enum.Enum):
    TASK_NAME = "task_name"
    OBJECTIVES = "objectives"

class TaskInfoSchema(Schema):
    title = fields.Str(required=True)
    description = fields.Str(required=False, allow_none=True)
    deadline = fields.Str(required=False, allow_none=True)

class AISuggestInputSchema(Schema):
    task_info = fields.Nested(TaskInfoSchema, required=True)
    mode = fields.Enum(
        AISuggestionMode,by_value=True, required=True, allow_none=False,
        metadata={
            "description": "生成モード",
            "enum": [m.value for m in AISuggestionMode],
        },
    )
class JobIdSchema(Schema):
    job_id = fields.Str(dump_only=True, required=True, metadata={"description": "Celery ジョブID。"})

class AsyncResultInfoSchema(Schema):
    class Meta:
        ordered = True

    job_id = fields.Str(
        required=True,
        metadata={
            "description": "Celery のジョブID（タスクの一意キー）。",
        },
    )
    state = fields.Str(
        required=True,
        validate=validate.OneOf(["PENDING", "STARTED", "RETRY", "FAILURE", "SUCCESS", "REVOKED"]),
        metadata={
            "description": "現在の実行状態。PENDING などの非完了状態の間は結果フィールドはありません。",
            "example": "PENDING",
        },
    )
    ready = fields.Bool(
        required=True,
        metadata={
            "description": "`True` のとき完了状態（成功/失敗いずれか）。",
            "example": False,
        },
    )
    successful = fields.Bool(
        required=True,
        metadata={
            "description": "`True` のときタスクは成功（state == SUCCESS）。",
            "example": False,
        },
    )
    date_done = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "完了日時（未完了時は null）。ISO8601。",
            "example": "2025-08-28T11:22:33Z",
        },
    )
    message = fields.Str(
        allow_none=True,
        metadata={
            "description": "失敗時などのメッセージ。成功時・未完了時は null の可能性あり。",
            "example": None,
        },
    )
# objectives 用1件
class ObjectiveItemSchema(Schema):
    class Meta:
        ordered = True

    title = fields.Str(
        required=True,
        metadata={
            "description": "目標タイトル。",
        },
    )
    assignee = fields.Str(
        allow_none=True,
        metadata={
            "description": "担当者名（生成提案）。",
        },
    )
    due_date = fields.Date(
        allow_none=True,
        metadata={
            "description": "目標期限（日付のみ、未設定の場合は null）。",
        },
    )



class ObjectivesSchema(Schema):
    objectives = fields.List(
        fields.Nested(ObjectiveItemSchema),
        required=False,
        metadata={
            "description": "AIが提案した目標の配列。mode='objectives' の完了時のみ出現。",
            "x-note": "mode='objectives' の完了レスポンス以外では本フィールドは含まれません。",
        },
    )
    raw_data = fields.Str(required=True, metadata={"description": "AIからの生データ。"})
    prompt = fields.Str(required=True, metadata={"description": "AIに送信したプロンプト。"})

class TaskTitleSchema(Schema):
    title = fields.Str(required=True, metadata={"description": "AIが提案したタスク名。"})
    raw_data = fields.Str(required=True, metadata={"description": "AIからの生データ。"})
    prompt = fields.Str(required=True, metadata={"description": "AIに送信したプロンプト。"})

class AIResultSchema(Schema):
    """
    AI結果取得エンドポイントのレスポンス統合スキーマ。

    ・未完了（PENDING/STARTED/RETRY 等）の場合:
        - async_result のみ返却（mode / task_title / objectives は欠落または null）
    ・完了 & mode == 'task_name' の場合:
        - async_result + mode='task_name' + task_title（AIが提案したタスク名）
    ・完了 & mode == 'objectives' の場合:
        - async_result + mode='objectives' + objectives[ObjectiveItem]
    """
    class Meta:
        ordered = True
    
    status = fields.Str(
        required=True,
        validate=validate.OneOf(["SUCCESS", "ERROR", "PENDING"]),
        metadata={
            "description": "処理の状態。'SUCCESS'（成功）, 'ERROR'（失敗）, 'PENDING'（未完了）のいずれか。",
        },
    )
    error = fields.Str(
        allow_none=True,
        metadata={
            "description": "エラーメッセージ。status が 'error' のときにのみ設定される想定。",
        },
    )

    async_result = fields.Nested(
        AsyncResultInfoSchema,
        required=True,
        metadata={
            "description": "Celery の AsyncResult 情報。未完了・成功・失敗の状態を示す共通ブロック。",
        },
    )

    mode = fields.Enum(
        AISuggestionMode,by_value=True, required=True, allow_none=False,
        metadata={
            "description": "生成モード。完了時のみ設定される想定。",
            "enum": [m.value for m in AISuggestionMode],
            },
    )

    # mode == "task_name" のときのみ返却
    task_title_data = fields.Nested(
        TaskTitleSchema,
        required=False,
        metadata={
            "description": "AIが提案したタスク名。mode='task_name' の完了時のみ出現。",
            "x-note": "mode='task_name' の完了レスポンス以外では本フィールドは含まれません。",
        },
    )

    # mode == "objectives" のときのみ返却
    objectives_data = fields.Nested(
        ObjectivesSchema,
        required=False,
        metadata={
            "description": "AIが提案した目標List。mode='objectives' の完了時のみ出現。",
            "x-note": "mode='objectives' の完了レスポンス以外では本フィールドは含まれません。",
        },
    )
