# Common Identity Hub 側 Task Progress Manager 連携設定手順

## 1. 目的

本ドキュメントは、Task Progress Manager（以下 TPM）で Common Identity Hub（以下 CIH）ログインを利用するために、**CIH / Keycloak 側で実施する必要がある設定・運用作業**を定義する。

TPM 側の認証連携仕様そのものは、以下を参照する。

- `docs/task-progress-manager_common-identity-hub_auth_spec.md`

対象実装:

- Repository: `TaroAnzai/task-progress-manager-monorepo`
- Branch: `develop`
- OIDC client ID: `task-progress-manager`
- Realm: `anzai-home`

---

## 2. CIH 側で必要な作業の概要

CIH 側では、主に以下を実施する。

1. Keycloak Realm `anzai-home` に TPM 用 OIDC Client を作成する。
2. Authorization Code Flow を有効にする。
3. Client Authentication を有効にし、confidential client とする。
4. TPM Backend の callback URL を Valid Redirect URI に登録する。
5. PKCE `S256` を利用できるようにする。可能であれば Keycloak 側でも `S256` を必須化する。
6. `openid email profile` に必要な標準 Client Scope / claim が利用できることを確認する。
7. Client Secret を発行し、TPM Backend 管理者へ安全に引き渡す。
8. TPM と初回自動紐付けする CIH User について、TPM と同じメールアドレスを設定し、メール検証済みにする。
9. OIDC ログインと初回紐付けが正常に動作することを確認する。

CIH が TPM の会社・組織・Role・AccessScope・Group・Task 権限を管理する必要はない。
これらの業務権限は引き続き TPM 側で管理する。

---

## 3. Keycloak Client 設定

### 3.1 基本設定

| 項目 | 設定値 |
| --- | --- |
| Realm | `anzai-home` |
| Client ID | `task-progress-manager` |
| Client protocol | OpenID Connect |
| Client authentication | ON |
| Client type | confidential |
| Standard Flow | ON |
| Direct Access Grants | OFF |
| Service Accounts | OFF |
| Implicit Flow | OFF |
| PKCE Code Challenge Method | `S256` |

TPM Backend は Client Secret を使用して Authorization Code を Token に交換するため、Public Client ではなく confidential client とする。

TPM Backend 自身も PKCE `S256` を指定して Authorization Request を開始する。

---

## 4. URL 設定

### 4.1 開発環境

TPM の `.env.example` に合わせた標準構成は以下とする。

| Keycloak 項目 | 開発環境の値 |
| --- | --- |
| Root URL | `http://localhost:5174` |
| Home URL | `http://localhost:5174/` |
| Valid Redirect URIs | `http://localhost:5000/sessions/oidc/callback` |
| Valid Post Logout Redirect URIs | 未使用。設定不要 |
| Web Origins | `http://localhost:5174` |

TPM 側の対応する設定:

```env
OIDC_ISSUER_URL=http://localhost:8080/realms/anzai-home
OIDC_CLIENT_ID=task-progress-manager
OIDC_CLIENT_SECRET=<CIHで発行したClient Secret>
OIDC_REDIRECT_URI=http://localhost:5000/sessions/oidc/callback
OIDC_FRONTEND_REDIRECT_URL=http://localhost:5174/
```

CIH のローカル Keycloak 公開ポートを `8080` 以外にしている場合は、`OIDC_ISSUER_URL` のみ実際の公開 URL に合わせる。

### 4.2 本番環境

本番では、**ブラウザから見える外部公開 URL** を設定する。

| Keycloak 項目 | 本番環境の値 |
| --- | --- |
| Root URL | `<TPM FrontendのOrigin>` |
| Home URL | `<TPM FrontendのURL>/` |
| Valid Redirect URIs | `<TPM Backendの外部公開URL>/sessions/oidc/callback` |
| Valid Post Logout Redirect URIs | 現仕様では未使用 |
| Web Origins | `<TPM FrontendのOrigin>` |

例:

```text
https://<backend-host>/<必要な公開prefix>/sessions/oidc/callback
```

Backend が Nginx 等の Reverse Proxy 配下で `/progress/api` のような prefix を持つ場合は、コンテナ内部 URL ではなく、**実際にブラウザから到達する callback の完全 URL** を登録する。

本番 TPM Backend 側では以下を設定する。

```env
OIDC_ISSUER_URL=https://auth.anzai-home.com/realms/anzai-home
OIDC_CLIENT_ID=task-progress-manager
OIDC_CLIENT_SECRET=<CIHで発行したClient Secret>
OIDC_REDIRECT_URI=<KeycloakのValid Redirect URIと完全一致するURL>
OIDC_FRONTEND_REDIRECT_URL=<TPM FrontendのURL>/
```

`OIDC_REDIRECT_URI` と Keycloak の Valid Redirect URI は一致させる。

---

## 5. Scope / Claim 要件

TPM は OIDC ログイン時に以下の scope を要求する。

```text
openid email profile
```

CIH / Keycloak から取得する認証情報には、少なくとも以下の claim が必要である。

| Claim | 用途 |
| --- | --- |
| `iss` | CIH Realm / Issuer の識別 |
| `sub` | CIH User の恒久的識別子 |
| `email` | 初回自動紐付け時の TPM User 検索 |
| `email_verified` | メール一致による自動紐付けを許可するための必須条件 |

`email` と `email_verified` が `email` scope で返ることを確認する。

TPM は最終的な恒久リンクにはメールアドレスを使用せず、以下の組み合わせを保存する。

```text
iss + sub
```

---

## 6. CIH User の準備

### 6.1 初回自動紐付けを行う場合

TPM User と CIH User がまだ紐付いていない場合、以下を満たす必要がある。

1. TPM 側に User が先に存在している。
2. CIH User のメールアドレスが TPM User のメールアドレスと一致している。
3. CIH User の `email_verified` が `true` になっている。
4. 同じメールアドレスに対応する有効な TPM User が1件だけ存在する。

条件を満たした最初の CIH ログイン時に、TPM が CIH の `iss + sub` を TPM User に保存して自動紐付けする。

### 6.2 CIH User だけを作成した場合

CIH User が存在しても、TPM User が存在しなければ TPM は利用できない。

CIH 認証成功を契機に TPM User を自動作成する処理は実装しない。

TPM User の Organization / Role / AccessScope 等は TPM 管理者が TPM 側で登録する。

---

## 7. Client Secret の取り扱い

`task-progress-manager` は confidential client のため Client Secret が必要である。

Client Secret は以下のルールで管理する。

- Git Repository に保存しない。
- README や本ドキュメントに実値を書かない。
- TPM 本番サーバーの `.env` にのみ設定する。
- 開発環境でも `OIDC_CLIENT_SECRET` は空欄にしない。
- Secret を変更した場合は CIH と TPM の設定変更を同時に行う。

TPM Backend は起動時・ログイン開始時に以下を必須設定として扱う。

```text
OIDC_ISSUER_URL
OIDC_CLIENT_ID
OIDC_CLIENT_SECRET
OIDC_REDIRECT_URI
OIDC_FRONTEND_REDIRECT_URL
```

---

## 8. CIH 管理 API を使用して Client を作成する場合

CIH Backend には System Administrator 用の OIDC Client 管理 API がある。

```text
POST /api/v1/admin/clients
```

作成例:

```json
{
  "client_id": "task-progress-manager",
  "name": "Task Progress Manager",
  "description": "Task Progress Manager OIDC client",
  "enabled": true,
  "public_client": false,
  "standard_flow_enabled": true,
  "direct_access_grants_enabled": false,
  "service_accounts_enabled": false,
  "redirect_uris": [
    "http://localhost:5000/sessions/oidc/callback"
  ],
  "web_origins": [
    "http://localhost:5174"
  ],
  "root_url": "http://localhost:5174",
  "base_url": "http://localhost:5174/",
  "admin_url": null
}
```

confidential client を作成した場合、作成レスポンスには初回の `client_secret` が返る。

その Secret を TPM の `OIDC_CLIENT_SECRET` に設定する。

### 8.1 PKCE 設定に関する注意

現行の CIH Admin Client API が公開している入力項目には、Keycloak の PKCE Code Challenge Method を設定する項目がない。

そのため、Keycloak 側でも PKCE `S256` を強制したい場合は、次のいずれかを行う。

1. Keycloak Admin Console で `task-progress-manager` Client の PKCE Code Challenge Method を `S256` に設定する。
2. 将来、CIH の Admin Client API を拡張し、Keycloak Client attributes の PKCE 設定を操作できるようにする。

TPM Backend 自体は Authorization Request で `S256` を使用する実装になっている。

---

## 9. Client Secret のローテーション

CIH Admin API には Client Secret のローテーション機能がある。

```text
POST /api/v1/admin/clients/task-progress-manager/rotate-secret
```

Secret をローテーションすると、旧 Secret を設定した TPM Backend では Token Exchange が失敗する。

ローテーション時は以下の順で実施する。

1. メンテナンス時間を決める。
2. CIH 側で Secret をローテーションする。
3. 新 Secret を TPM 本番 `.env` の `OIDC_CLIENT_SECRET` に反映する。
4. TPM Backend を再起動する。
5. CIH ログインを実施し、Token Exchange が成功することを確認する。

---

## 10. 動作確認

CIH 側設定完了後、以下を確認する。

### 10.1 Discovery

TPM から以下へ到達できること。

```text
https://auth.anzai-home.com/realms/anzai-home/.well-known/openid-configuration
```

開発環境では設定したローカル Keycloak URLを使用する。

### 10.2 初回リンク

1. TPM に User を作成する。
2. 同じ email の CIH User を作成し、メール検証済みにする。
3. TPM ログイン画面から「Common Identity Hub でログイン」を選択する。
4. Keycloak でログインする。
5. TPM に正常に戻ることを確認する。
6. TPM User に CIH の `identity_issuer` / `identity_subject` が保存されていることを確認する。
7. 2回目以降は email 検索ではなく `iss + sub` で同じ TPM User にログインできることを確認する。

### 10.3 拒否ケース

以下も確認する。

- CIH User はあるが TPM User がない → TPM 利用不可。
- `email_verified=false` → 初回自動紐付け不可。
- 無効化・削除済み TPM User → 利用不可。
- 別 TPM User に既に紐付いた CIH identity → 競合として拒否。

### 10.4 既存認証との併用

CIH 連携後も TPM の既存 email/password ログインが利用できることを確認する。

CIH のパスワードと TPM のローカルパスワードは同期しない。

---

## 11. 運用上の重要事項

### 11.1 Realm / Issuer URL を安易に変更しない

TPM は CIH User を以下で識別する。

```text
identity_issuer + identity_subject
```

Realm 名や Keycloak の公開 Issuer URL を変更すると `iss` が変わり、既存リンクに影響する。

本番運用開始後は、`https://auth.anzai-home.com/realms/anzai-home` を安易に変更しない。

### 11.2 CIH User の削除・再作成に注意する

Keycloak User を削除して同じメールアドレスで作り直しても、通常は `sub` が変わる。

TPM User に旧 `iss + sub` が保存されている状態では、新しい CIH User をメール一致だけで自動的に再リンクしない。

CIH User を再作成した場合は、TPM 側の identity link を管理者が確認・解除・再設定する運用が必要になる。

### 11.3 メール変更

一度 `iss + sub` で紐付いた後は、メールアドレスは恒久的な認証キーとして使用しない。

そのため CIH User のメール変更だけで既存の OIDC link が切れることはない。
ただし TPM 側の業務メールとして同じ値を維持する必要があるかどうかは、TPM のユーザー管理方針に従う。

### 11.4 TPM の権限を CIH に持たせない

以下は TPM 側で管理する。

- Company
- Organization
- Role
- AccessScope
- Group
- Task / Objective / Progress に関する権限

CIH / Keycloak Role を TPM の業務 Role として同期する処理は本連携では行わない。

### 11.5 TPM ログアウトは CIH 全体ログアウトではない

TPM のログアウトは TPM の Flask Session のみを終了する。

Keycloak の SSO Session は残すため、再度「Common Identity Hub でログイン」を選ぶと SSO により認証画面を省略してログインできる場合がある。

現仕様では Keycloak の Post Logout Redirect URI は使用しない。

---

## 12. CIH 側のコード変更要否

現在の CIH には以下が既に実装されている。

- OIDC Client 作成 API
- OIDC Client 更新 API
- OIDC Client 削除 API
- confidential client の Client Secret 取得
- Client Secret ローテーション

したがって、**TPM 連携のためだけに CIH Backend のコード変更は必須ではない**。

ただし、CIH Admin API から PKCE `S256` の強制設定まで一元管理したい場合は、Client 管理 API の拡張を検討する。

---

## 13. 作業完了チェックリスト

- [ ] Realm `anzai-home` に `task-progress-manager` Client を作成した。
- [ ] Client authentication を ON にした。
- [ ] Standard Flow を ON にした。
- [ ] Direct Access Grants を OFF にした。
- [ ] Service Accounts を OFF にした。
- [ ] Valid Redirect URI を TPM Backend の外部 callback URL に設定した。
- [ ] Web Origin を TPM Frontend の Origin に設定した。
- [ ] PKCE `S256` を利用する設定を確認した。
- [ ] `email` / `email_verified` claim が返ることを確認した。
- [ ] Client Secret を TPM Backend の `OIDC_CLIENT_SECRET` に設定した。
- [ ] TPM の `OIDC_ISSUER_URL` が CIH Realm の Issuer と一致している。
- [ ] verified email が一致する TPM User / CIH User で初回リンクを確認した。
- [ ] 2回目以降の CIH ログインを確認した。
- [ ] TPM User がない CIH User が拒否されることを確認した。
- [ ] TPM の既存 email/password ログインが引き続き利用できることを確認した。
