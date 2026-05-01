---

# ✅ **`docs/error_handling.md`（修正版）**

```markdown
# Error Handling Policy

本ドキュメントは、**Flask-Smorest + Marshmallow** を用いたRESTful API開発における  
**エラーハンドリングとステータスコード運用の標準方針**をまとめたものです。

---

## ✅ 基本方針

1. **RESTful API標準に準拠**したステータスコードを使用する。
2. **スキーマ層（Marshmallow）**は入力形式エラーのみ、  
   **サービス層**はビジネスロジック・権限・整合性エラーを担当。
3. **422 Unprocessable Entity はスキーマ専用**とし、  
   サービス層では使用せず **400/409** を使用する。
4. **エラーレスポンス形式は統一**する。

---

## ✅ ステータスコード運用表

| ステータスコード | 使用タイミング | 例 | サービス層での例外クラス |
|------------------|--------------|----|------------------------|
| **400 Bad Request** | ビジネスロジック上の不正リクエスト | 期日が過去日付、階層構造違反 | `ServiceValidationError` |
| **401 Unauthorized** | 未ログイン、トークン無効 | ログイン必須APIへの未認証アクセス |（ルート層で自動処理）|
| **403 Forbidden** | 認証済みだが権限不足 | 組織外リソースへの操作 | `ServicePermissionError` |
| **404 Not Found** | リソースが存在しない | ID指定リソースが未登録 | `ServiceNotFoundError` |
| **409 Conflict** | 状態が既存データと衝突 | 重複登録、既に削除済み | `ServiceConflictError` |
| **422 Unprocessable Entity** | **Marshmallowのスキーマバリデーション専用** | 型不一致、必須項目不足 |（サービス層では使用しない）|
| **500 Internal Server Error** | 想定外エラー | DB障害、未捕捉例外 |（ルート層で自動処理）|

---

## ✅ エラーレスポンス形式（統一仕様）

```json
{
  "status": "error",
  "code": 400,
  "message": "期日は今日以降である必要があります",
  "details": {
    "field": "due_date"
  }
}
```

* **status**：固定で `"error"`
* **code**：HTTPステータスコード
* **message**：ユーザー向けメッセージ（日本語可）
* **details**：任意（詳細情報、デバッグ向け）

---

## ✅ Flask-Smorestでの実装例

### **1. 共通エラークラス**

```python
# app/errors.py
class ServiceNotFoundError(Exception):
    pass

class ServicePermissionError(Exception):
    pass

class ServiceConflictError(Exception):
    pass

class ServiceValidationError(Exception):
    pass
```

### **2. ルート層でのエラーハンドラ**

```python
from flask_smorest import abort
from app.errors import (
    ServiceNotFoundError,
    ServicePermissionError,
    ServiceConflictError,
    ServiceValidationError
)

@bp.errorhandler(ServiceNotFoundError)
def handle_not_found_error(e):
    abort(404, message=str(e))

@bp.errorhandler(ServicePermissionError)
def handle_permission_error(e):
    abort(403, message=str(e))

@bp.errorhandler(ServiceConflictError)
def handle_conflict_error(e):
    abort(409, message=str(e))

@bp.errorhandler(ServiceValidationError)
def handle_validation_error(e):
    abort(422, message=str(e))
```

---

## ✅ サービス層での使用例

```python
from app.errors import (
    ServiceNotFoundError,
    ServicePermissionError,
    ServiceConflictError,
    ServiceValidationError
)

def update_task(task_id, data, current_user):
    task = db.session.get(Task, task_id)
    if not task:
        raise ServiceNotFoundError("タスクが見つかりません")

    if not check_org_access(current_user, task.organization_id):
        raise ServicePermissionError("権限がありません")

    if Task.query.filter_by(title=data["title"], organization_id=task.organization_id).first():
        raise ServiceConflictError("同じタイトルのタスクが既に存在します")

    if data["due_date"] < date.today():
        raise ServiceValidationError("期日は今日以降である必要があります")

    # 更新処理...
    db.session.commit()
    return task
```

---

## ✅ 関連ドキュメント

* [Service Validation Order](./service_validation_order.md)（サービス層でのバリデーション順序）
* [Development Guidelines](./development-guidelines.md)（全体方針）

---

この方針に従うことで、
**フロントエンド開発者がエラー内容を統一的に解釈でき、保守性が高いAPI**を実現できます。

---

### ✅ **次の提案**

1. **`development-guidelines.md` に、今作成した `service_validation_order.md` と `error_handling.md` へのリンクを追記するサンプル**
2. **README.md に「docsへの誘導リンク」を追記するサンプル**

👉 両方作りますか？それとも **`development-guidelines.md` だけ先に提示**しましょうか？
