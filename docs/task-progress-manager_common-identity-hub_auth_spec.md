# Task Progress Manager

# Common Identity Hub 認証連携仕様書

## 既存ローカル認証を維持した OIDC / SSO 連携

### 対象システム

* `task-progress-manager-monorepo`
* `common-identity-hub`

### 認証基盤

Common Identity Hub
Keycloak / OpenID Connect

### 基本方針

Task Progress Manager の既存 email/password 認証を恒久的に残し、Common Identity Hub を追加認証方式として併用する。

### 業務ユーザー管理

会社・組織・Role・AccessScope・Group・Task権限は Task Progress Manager 側で管理する。

---

# 1. 目的

本仕様は、Task Progress Manager（以下 TPM）の既存ユーザー管理・ローカルログインを維持したまま、Common Identity Hub（以下 CIH）を OpenID Connect（OIDC）による追加の認証手段として連携するための仕様を定義する。

CIH は「本人が誰であるか」を認証し、TPM は「その本人が TPM を利用できるか」「どの会社・組織に所属し、どの権限を持つか」を管理する。

---

# 2. 基本方針

* TPM の既存 email/password ログインは廃止しない。CIH 連携後も利用可能とする。
* TPM の User を業務アカウントの正本とする。
* CIH ユーザーが存在するだけでは TPM を利用可能にしない。
* CIH 連携は TPM User に対する追加のログイン方法として扱う。
* CIH で認証したユーザーは、TPM User と紐付いている場合のみ TPM にログインできる。
* 会社、組織、Role、AccessScope、Group、Task 権限等は CIH に移さず TPM 側で管理する。
* TPM の既存 API は Flask-Login の `current_user` を継続利用する。
* OIDC ログイン成功時も最終的には `login_user(user)` に集約する。

---

# 3. 現行実装

## 3.1 ユーザー登録

現行の TPM では、System Admin または Organization Admin がユーザーを登録する。

登録対象組織に対して ORG_ADMIN 相当のアクセス権限を持つことが必要である。

```text
POST /users

入力:
- name
- email
- password
- organization_id
- role
```

ユーザー作成時に User レコードを作成し、その場で password をハッシュ化して `password_hash` に保存する。

続いて同じ `organization_id` に対する AccessScope を作成し、role を設定する。

```text
User
  name
  email
  normalized_email
  password_hash
  organization_id

AccessScope
  user_id
  organization_id
  role
```

---

## 3.2 現行ログイン

```text
POST /sessions
  email + password
      ↓
User.normalized_email を検索
      ↓
User.check_password()
      ↓
Flask-Login login_user(user)
      ↓
Session Cookie
```

ログイン後の各 API は、

```python
@login_required
current_user
```

を使用している。

この構造は CIH 連携後も維持する。

---

## 3.3 パスワード再設定

```text
POST /auth/password-reset/request
POST /auth/password-reset/confirm
```

TPM は独自にパスワード再設定メールを送信し、再設定トークンを検証した後に `User.set_password()` を実行する。

CIH 連携後もローカルログインを維持するため、この機能も残す。

---

# 4. 目標アーキテクチャ

```text
                    ┌──────────────────────────────┐
                    │ Common Identity Hub / Keycloak│
                    │  - OIDC                       │
                    │  - SSO                        │
                    │  - CIH側パスワード/MFA        │
                    └──────────────┬───────────────┘
                                   │
                              OIDC │
                                   ▼
┌──────────────────────────────────────────────────────────┐
│                Task Progress Manager                     │
│                                                          │
│ User                                                     │
│  - id                                                    │
│  - email                                                 │
│  - password_hash  ────── Local Login                     │
│  - organization_id                                      │
│  - identity_issuer  ─┐                                   │
│  - identity_subject ─┴──── CIH Login                     │
│                                                          │
│ AccessScope / Organization / Group / Task permissions    │
└──────────────────────────────────────────────────────────┘
```

---

# 5. ユーザーと認証方式の考え方

TPM User は1人につき1レコードとし、その1レコードに複数の認証方法を持たせる。

CIH 連携したからといって別の TPM User を作成しない。

| TPM User | ローカルPW | CIH User | CIH連携 | 利用可否 / 動作              |
| -------- | ------ | -------- | ----- | ---------------------- |
| あり       | あり     | なし       | なし    | TPMローカルログイン可能          |
| あり       | あり     | あり       | なし    | TPMログイン可能。CIHから初回連携可能  |
| あり       | あり     | あり       | あり    | TPM / CIH のどちらでもログイン可能 |
| あり       | なし     | あり       | あり    | CIHログインのみ可能（将来拡張）      |
| なし       | -      | あり       | -     | CIH認証は成功してもTPM利用不可     |

---

# 6. TPM User と CIH User の紐付け

## 6.1 識別子

CIH ユーザーとの恒久的な紐付けにはメールアドレスを使用せず、OIDC の `issuer`（`iss`）と `subject`（`sub`）の組み合わせを使用する。

```text
identity_issuer
  = https://auth.anzai-home.com/realms/anzai-home

identity_subject
  = <OIDC sub>
```

メールアドレスは変更される可能性があるため、恒久的な認証IDとして使用しない。

---

## 6.2 DB変更

User に以下を追加する。

```text
User
  identity_issuer:   VARCHAR(255) NULL
  identity_subject:  VARCHAR(255) NULL
```

一意制約を追加する。

```text
UNIQUE(identity_issuer, identity_subject)
```

既存ユーザーは CIH 未連携状態を表すため NULL を許容する。

---

## 6.3 初回自動リンク

CIH でログインした際、`issuer + subject` に一致する TPM User が存在しない場合、OIDC の `email_verified` が `true` であれば verified email を用いて既存 TPM User を検索し、自動リンクを許可する。

```text
1. issuer + sub で TPM User を検索
   ├─ 見つかる
   │    ↓
   │  ログイン
   │
   └─ 見つからない
        ↓

2. email_verified == true を確認
        ↓

3. normalized_email が一致する TPM User を検索
   ├─ 1件見つかる
   │    ↓
   │  issuer + sub を保存
   │    ↓
   │  ログイン
   │
   └─ 見つからない
        ↓
      利用登録なし
```

`email_verified == false` の場合、メール一致だけで自動リンクしてはならない。

---

# 7. 認証エンドポイント

## 7.1 既存エンドポイント

| Method | Path                           | 用途                      | 扱い |
| ------ | ------------------------------ | ----------------------- | -- |
| POST   | `/sessions`                    | TPM email/password ログイン | 維持 |
| GET    | `/sessions/current`            | 現在ログイン中のTPM User取得      | 維持 |
| DELETE | `/sessions/current`            | TPMセッションのログアウト          | 維持 |
| POST   | `/auth/password-reset/request` | TPMローカルPW再設定要求          | 維持 |
| POST   | `/auth/password-reset/confirm` | TPMローカルPW再設定            | 維持 |

---

## 7.2 新規エンドポイント

| Method | Path                      | 用途                                                             |
| ------ | ------------------------- | -------------------------------------------------------------- |
| GET    | `/sessions/oidc/login`    | CIH / Keycloak の Authorization Endpoint へリダイレクト                |
| GET    | `/sessions/oidc/callback` | Authorization Code を受け取り、Token取得・claims検証・TPM User特定・Flaskログイン |

---

## 7.3 GET `/sessions/oidc/login`

CIHログイン開始用エンドポイント。

処理内容:

* OIDC Discovery から `authorization_endpoint` を取得する。
* `state` を生成してセッションに保存する。
* PKCE を使用する場合は `code_verifier` / `code_challenge` を生成する。
* `redirect_uri` として `/sessions/oidc/callback` を指定する。
* Keycloak のログイン画面へ 302 Redirect する。

---

## 7.4 GET `/sessions/oidc/callback`

CIHログイン完了後のコールバック。

```text
callback
  ↓
state 検証
  ↓
authorization code を token_endpoint で交換
  ↓
ID Token / UserInfo を検証
  ↓
iss + sub を取得
  ↓
TPM User 特定
  ↓
必要なら verified email で初回リンク
  ↓
login_user(tpm_user)
  ↓
TPMフロントへリダイレクト
```

---

# 8. CIHログイン時の判定仕様

| 条件                                                       | 結果            |
| -------------------------------------------------------- | ------------- |
| issuer + sub に一致する有効な TPM User が存在                       | ログイン成功        |
| issuer + sub は未登録、email_verified=true、email一致TPM Userが1件 | 自動リンクしてログイン成功 |
| issuer + sub は未登録、email_verified=false                   | 自動リンク禁止。利用不可  |
| CIH Userは存在するがTPM Userなし                                 | 認証成功・利用不可     |
| TPM Userが soft delete / 無効                               | 利用不可          |
| 同一 issuer + sub が別Userに既に紐付く                             | 競合エラー。自動変更しない |

---

# 9. TPM User が存在しない場合

CIH の認証に成功しても、TPM User が存在しない場合は TPM User を自動作成しない。

理由は、TPM User 作成時に以下の業務情報が必要だからである。

```text
company
organization
role
AccessScope
```

CIH だけではこれらを決定できない。

```text
CIH 認証成功
      ↓
TPM User なし
      ↓
403 相当 / 利用登録なし
      ↓
「Task Progress Manager の利用登録がありません。
  管理者にお問い合わせください。」
```

---

# 10. TPMユーザー登録仕様への影響

初期実装では既存のユーザー登録仕様を変更しない。

組織管理者は従来通り、

```text
name
email
password
organization_id
role
```

を指定してユーザーを作成する。

したがって、CIH アカウントを持たない利用者でも従来通り TPM を使用できる。

CIH アカウントを後から作成した場合は、CIHログイン時に紐付けできる。

将来的に「CIH専用ユーザー」を作成したい場合は password を任意化し、認証方式を選択できる設計を追加検討する。

これは本仕様の初期実装範囲外とする。

---

# 11. ログイン画面

```text
Task Progress Manager

[ Common Identity Hub でログイン ]

──────────── または ────────────

メールアドレス
[                              ]

パスワード
[                              ]

[ ログイン ]

パスワードを忘れた場合
```

CIHと未連携のユーザー、CIHアカウントを持たないユーザーのため、ローカルログインUIは恒久的に表示する。

---

# 12. ログアウト

`DELETE /sessions/current` は TPM の Flask セッションのみを終了する。

CIH / Keycloak の SSO セッションは原則として終了しない。

理由は、CIH は複数システムで共有されるため、TPM からログアウトしただけで他システムの SSO セッションまで終了させるべきではないためである。

必要に応じて将来、

```text
Common Identity Hubからもログアウト
```

という別操作を追加し、Keycloak の `end_session_endpoint` を利用する。

---

# 13. セキュリティ要件

* OIDC Authorization Code Flow を使用する。
* 可能であれば PKCE を使用する。
* `state` を必ず検証し、CSRF を防止する。
* ID Token の署名を検証する。
* `iss` を検証する。
* `aud` を検証する。
* `exp` を検証する。
* `nonce` を使用する場合は検証する。
* 自動リンクにメールを使う場合は `email_verified=true` を必須とする。
* `issuer + subject` の一意制約を設ける。
* CIHログインだけで TPM User を自動作成しない。
* 既存の TPM `password_hash` と CIH のパスワードを同期しない。
* TPMローカルパスワードとCIHパスワードは完全に独立した Credential として扱う。

---

# 14. エラー仕様

| ケース         | 想定メッセージ / 処理                                                    |
| ----------- | --------------------------------------------------------------- |
| CIH認証失敗     | Common Identity Hub でのログインに失敗しました。                              |
| TPM利用登録なし   | ログインには成功しましたが、Task Progress Manager の利用登録がありません。管理者にお問い合わせください。 |
| 未検証メールで未リンク | 安全のため自動連携しない                                                    |
| Identity競合  | このCommon Identity Hubアカウントは別のユーザーに連携されています。                     |
| 無効化TPM User | このユーザーは現在利用できません。                                               |
| state不一致    | 認証リクエストが無効です。再度ログインしてください。                                      |

---

# 15. 実装範囲

## 15.1 必須

* User に `identity_issuer` / `identity_subject` を追加するDBマイグレーション。
* Common Identity Hub の Keycloak に `task-progress-manager` OIDC Client を作成する。
* `GET /sessions/oidc/login` を追加する。
* `GET /sessions/oidc/callback` を追加する。
* `issuer + sub` による User 特定処理を追加する。
* verified email による初回自動リンク処理を追加する。
* CIHログイン成功後に `login_user(user)` を実行し、既存Flask-Loginへ接続する。
* フロントログイン画面に「Common Identity Hubでログイン」ボタンを追加する。
* 利用登録なし・競合・認証失敗時のエラー画面またはメッセージを追加する。

---

## 15.2 変更しないもの

* `POST /sessions` のローカルログイン。
* 既存の `User.password_hash`。
* パスワードリセット機能。
* Organization / Company / AccessScope / Role の管理。
* Group / Task / Objective 等の権限制御。
* 各APIの `@login_required` / `current_user` ベースの認証処理。

---

## 15.3 将来拡張

* ログイン済みTPMユーザーが明示的にCIHアカウントを連携する `/sessions/oidc/link`。
* CIH連携解除。
* CIH専用ユーザー作成。
* User登録時の password 任意化。
* TPM管理者画面でCIH連携状態を確認する機能。
* 管理者による手動紐付け。
* CIHからもログアウトする全体ログアウト。

---

# 16. テスト観点

| No. | テスト内容                        | 期待結果                       |
| --- | ---------------------------- | -------------------------- |
| 1   | 既存email/passwordでログイン        | 従来通りログイン成功                 |
| 2   | CIH連携済UserでCIHログイン           | 同一TPM Userでログイン成功          |
| 3   | CIH未連携・verified email一致      | 自動リンク後ログイン成功               |
| 4   | CIH未連携・email未検証              | 自動リンクされず利用不可               |
| 5   | CIH Userあり、TPM Userなし        | TPM利用不可                    |
| 6   | CIH連携済Userをローカル認証            | ログイン成功                     |
| 7   | 同じCIH identityを別TPM Userへリンク | 一意制約または業務チェックで拒否           |
| 8   | TPMログアウト後CIHセッションが残っている      | TPMだけログアウト。再CIHログイン時はSSO可能 |
| 9   | ローカルPW再設定                    | 既存仕様通り成功                   |
| 10  | CIH側PW変更                     | TPMローカルPWには影響しない           |

---

# 17. 最終仕様の要点

* TPMの既存アカウントは廃止しない。
* TPMの既存ログインも廃止しない。
* CIHはTPM Userに対する追加のSSO認証方式として実装する。
* TPM Userが存在しないCIHユーザーはTPMを利用できない。
* CIHとTPMが未連携でも、TPMのemail/passwordがあれば従来通り利用できる。
* CIH連携後はローカルログインとCIHログインの双方を利用可能とする。
* 業務権限はTPM、共通本人認証はCIHという責務分離を維持する。

---

# 付録A. 推奨処理フロー

## Local Login

```text
POST /sessions
    ↓
email/password 検証
    ↓
TPM User
    ↓
login_user()
    ↓
既存API
```

## CIH Login

```text
GET /sessions/oidc/login
    ↓
Keycloak
    ↓
GET /sessions/oidc/callback
    ↓
OIDC token validation
    ↓
issuer + sub 検索
    │
    ├─ Hit
    │    ↓
    │  TPM User
    │
    └─ Miss
         ↓
       email_verified?
         │
         ├─ Yes
         │    ↓
         │  email一致User検索
         │    ↓
         │  link
         │
         └─ No
              ↓
            利用不可
    ↓
login_user()
    ↓
既存API
```

---

# 付録B. 推奨Userモデル差分

```python
class User(...):
    id
    name
    email
    normalized_email
    password_hash

    organization_id
    is_superuser

    # OIDC identity
    identity_issuer      # nullable
    identity_subject     # nullable

    # Existing relationships
    access_scopes
    task_orders
    created_tasks
    task_access
```
