# Service Layer Validation Order

本ドキュメントは、**Flask-Smorest + Marshmallow** を用いたRESTful API開発において、  
**サービス層（Service Layer）で実施すべきバリデーションの理想的な順序**をまとめたものです。

---

## ✅ バリデーションの基本方針

- **早期終了（Fail Fast）**：判定可能なものから順に検証することで無駄な処理を防ぐ。
- **RESTful APIのステータスコード標準**に準拠する。
- **422 Unprocessable Entity は Marshmallow（スキーマバリデーション）のみで使用**し、  
  サービス層では使用しない。

---

## ✅ バリデーション実施順序（理想）

### **① 404 Not Found（リソース存在確認）**

* **目的**：対象となるリソースが存在するかを最初に確認する。
* **例**：

  * 指定IDのユーザー/タスクが存在しない
  * 関連リソース（親オブジェクト、外部キー先）が存在しない
* **サンプルコード**：

  ```python
  task = db.session.get(Task, task_id)
  if not task:
      raise ServiceNotFoundError("タスクが見つかりません")  # → HTTP 404
  ```

---

### **② 403 Forbidden（権限・スコープ確認）**

* **目的**：リソースが存在する場合、現在のユーザーに操作権限があるか確認する。
* **例**：

  * 自分の組織外のリソースにアクセスしていないか
  * ロールが十分か（例：ORG\_ADMIN、SYSTEM\_ADMIN）
* **サンプルコード**：

  ```python
  if not check_org_access(current_user, task.organization_id, OrgRoleEnum.ORG_ADMIN):
      raise ServicePermissionError("権限がありません")  # → HTTP 403
  ```

---

### **③ 409 Conflict（状態衝突・整合性違反）**

* **目的**：リソースは存在し、権限もあるが、状態が既存データと矛盾しないか確認する。
* **例**：

  * 同じメールアドレスや組織コードが既に存在する
  * 削除済みフラグが立っているものを再度削除しようとした
* **サンプルコード**：

  ```python
  if Task.query.filter_by(title=data["title"], organization_id=org_id).first():
      raise ServiceConflictError("同じタイトルのタスクが既に存在します")  # → HTTP 409
  ```

---

### **⑤ 500 Internal Server Error（想定外例外）**

* **目的**：上記以外の想定外エラーは、ルート層の`@errorhandler`で一括処理。
* **推奨**：サービス層ではtry/exceptを極力書かず、共通ハンドリングに任せる。

---

## ✅ 推奨フローチャート

```
┌─────────────┐
│① リソース存在確認│
└─────┬───────┘
      │存在しない → 404
      ▼
┌─────────────┐
│② 権限確認        │
└─────┬───────┘
      │権限なし → 403
      ▼
┌─────────────┐
│③ 状態衝突確認    │
└─────┬───────┘
      │衝突あり → 409
      ▼
┌─────────────┐
│④ ビジネスルール確認│
└─────┬───────┘
      │違反あり → 400
      ▼
    （処理続行）
```

---


