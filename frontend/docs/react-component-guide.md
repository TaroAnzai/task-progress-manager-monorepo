# React コンポーネント コーディングガイド

このドキュメントでは、React コンポーネントを作成する際のベストプラクティスとコーディング順序について説明します。

## 基本構造の概要

```
1. Import文
2. 型定義
3. コンポーネント外の定数・ヘルパー関数
4. メインコンポーネント
   ├── フック呼び出し
   ├── useEffect
   ├── 早期return（ガード節）
   └── メインのJSXレンダリング
```

## 1. Import文の順序

### 推奨順序
```typescript
// 1. React関連（最優先）
import React, { useState, useEffect, useCallback, useMemo } from 'react';

// 2. 外部ライブラリ
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';
import axios from 'axios';

// 3. 内部モジュール - フック
import { useUser } from '@/hooks/useUser';
import { useAuth } from '@/hooks/useAuth';

// 4. 内部モジュール - コンポーネント
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/Modal';

// 5. 内部モジュール - ユーティリティ
import { formatDate } from '@/utils/date';
import { API_ENDPOINTS } from '@/constants/api';
```

### ルール
- **React関連を最初に配置**
- **外部ライブラリ** → **内部モジュール**の順
- 内部モジュール内では**機能別**に分類
- アルファベット順での並び替えを推奨

## 2. 型定義

```typescript
// Props型は必須
interface ComponentProps {
  userId: string;
  showDetails?: boolean;
  onUpdate?: (data: User) => void;
}

// コンポーネント内で使用する型
interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

// Form用の型
interface EditForm {
  name: string;
  email: string;
}
```

### ベストプラクティス
- **Props型は必須で定義**
- オプショナルプロパティには`?`を使用
- 複雑な型は別ファイルに分離を検討

## 3. コンポーネント外の定数・関数

```typescript
// 定数
const DEFAULT_PAGE_SIZE = 10;
const MAX_RETRY_COUNT = 3;

// ヘルパー関数
const formatUserName = (user: User): string => {
  return user.name || 'Unknown User';
};

const validateEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};
```

### ルール
- **コンポーネント外で定義**（再レンダリング時の再作成を防ぐ）
- **UPPER_SNAKE_CASE**で定数を定義
- 純粋関数として実装

## 4. フック呼び出しの順序

```typescript
export default function UserProfile({ userId, showPosts, onUpdate }: UserProfileProps) {
  // 4-1. 基本的なstate管理フック
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<EditForm>({ name: '', email: '' });
  
  // 4-2. 外部状態管理・ルーター系フック
  const router = useRouter();
  const { user: currentUser } = useAuth();
  
  // 4-3. カスタムフック（データ取得系）
  const { user, isLoading: isUserLoading, error } = useUser(userId);
  const { posts, isLoading: isPostsLoading } = useUserPosts(userId);
  
  // 4-4. 計算値（useMemo）
  const displayName = useMemo(() => {
    return user ? formatUserName(user) : '';
  }, [user]);
  
  const totalPostsCount = useMemo(() => {
    return posts?.length || 0;
  }, [posts]);
  
  // 4-5. イベントハンドラー（useCallback）
  const handleEdit = useCallback(() => {
    setIsEditing(true);
    if (user) {
      setFormData({ name: user.name, email: user.email });
    }
  }, [user]);
  
  const handleSave = useCallback(async () => {
    // 保存処理
  }, [formData, user]);
  
  // 4-6. 副作用（useEffect）
  // ... useEffect は次のセクションで詳説
}
```

### フック順序のルール
1. **useState** - 基本的な状態管理
2. **外部フック** - useRouter, 状態管理ライブラリなど
3. **カスタムフック** - データ取得、ビジネスロジック
4. **useMemo** - 計算値のメモ化
5. **useCallback** - イベントハンドラーのメモ化
6. **useEffect** - 副作用処理

## 5. useEffect の配置ルール

```typescript
// 5-1. 初回マウント時のみ（依存配列: []）
useEffect(() => {
  console.log('Component mounted');
  // 初期化処理
}, []);

// 5-2. 単一の依存関係
useEffect(() => {
  if (user) {
    setFormData({ name: user.name, email: user.email });
  }
}, [user]);

// 5-3. 複数の依存関係（少ない順）
useEffect(() => {
  if (user && router.isReady) {
    // 複合的な処理
  }
}, [user, router.isReady]);

// 5-4. クリーンアップが必要な処理
useEffect(() => {
  const timer = setInterval(() => {
    // 定期処理
  }, 1000);
  
  return () => clearInterval(timer);
}, []);
```

### useEffect のベストプラクティス
- **依存配列の項目数が少ない順**に配置
- **関連する機能**は近くにまとめる
- **クリーンアップ処理**を忘れずに記述
- **ESLintのexhaustive-deps**ルールに従う

## 6. 早期return（ガード節）

```typescript
// ローディング状態
if (isUserLoading || isPostsLoading) {
  return <LoadingSpinner />;
}

// エラー状態
if (error) {
  return <ErrorMessage message={error.message} />;
}

// データ不足
if (!user) {
  return <EmptyState message="ユーザーが見つかりません" />;
}

// メインのJSXレンダリング
return (
  <div className="user-profile">
    {/* メインコンテンツ */}
  </div>
);
```

### ガード節のポイント
- **ローディング状態を最初に**チェック
- **エラー状態**を次にチェック
- **必須データの存在確認**
- メインロジックでは**データの存在が保証**される

## 7. JSXレンダリングの構造

```typescript
return (
  <div className="component-root">
    {/* 7-1. メイン情報表示 */}
    <header className="component-header">
      <h1>{displayName}</h1>
    </header>
    
    {/* 7-2. 条件付きレンダリング */}
    {isEditing ? (
      <EditForm 
        data={formData}
        onChange={setFormData}
        onSave={handleSave}
        onCancel={() => setIsEditing(false)}
      />
    ) : (
      <UserDetails user={user} onEdit={handleEdit} />
    )}
    
    {/* 7-3. オプショナルなセクション */}
    {showPosts && posts && (
      <PostsList posts={posts} />
    )}
  </div>
);
```

## 8. 命名規則

### 状態関連
```typescript
const [isLoading, setIsLoading] = useState(false);      // boolean: is + 形容詞
const [hasError, setHasError] = useState(false);        // boolean: has + 名詞
const [userCount, setUserCount] = useState(0);          // number: 名詞
const [selectedUser, setSelectedUser] = useState(null); // object: 形容詞 + 名詞
```

### イベントハンドラー
```typescript
const handleClick = useCallback(() => {}, []);          // handle + 動作
const handleFormSubmit = useCallback(() => {}, []);     // handle + 対象 + 動作
const handleUserSelect = useCallback(() => {}, []);     // handle + 対象 + 動作
```

### カスタムフック
```typescript
const { user, isLoading, error } = useUser(userId);     // use + 対象
const { data: posts } = useUserPosts(userId);           // エイリアスで明確化
```

## 9. パフォーマンス最適化

### useMemo の使用例
```typescript
// 重い計算処理
const expensiveValue = useMemo(() => {
  return processLargeData(rawData);
}, [rawData]);

// オブジェクトの作成
const userDisplayInfo = useMemo(() => ({
  name: formatUserName(user),
  avatar: user?.avatar || DEFAULT_AVATAR,
  lastLogin: formatDate(user?.lastLoginAt)
}), [user]);
```

### useCallback の使用例
```typescript
// 子コンポーネントに渡すイベントハンドラー
const handleUserClick = useCallback((userId: string) => {
  router.push(`/users/${userId}`);
}, [router]);

// フォーム処理
const handleFormChange = useCallback((field: string, value: string) => {
  setFormData(prev => ({ ...prev, [field]: value }));
}, []);
```

## 10. 完全なコンポーネント例

```typescript
// 1. Import文
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/router';
import { toast } from 'react-hot-toast';
import { useUser } from '@/hooks/useUser';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';

// 2. 型定義
interface UserProfileProps {
  userId: string;
  showPosts?: boolean;
  onUserUpdate?: (user: User) => void;
}

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

// 3. 定数・ヘルパー関数
const formatUserName = (user: User): string => {
  return user.name || 'Unknown User';
};

// 4. メインコンポーネント
export default function UserProfile({ 
  userId, 
  showPosts = true, 
  onUserUpdate 
}: UserProfileProps) {
  
  // 4-1. useState
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', email: '' });
  
  // 4-2. 外部フック
  const router = useRouter();
  
  // 4-3. カスタムフック
  const { user, isLoading, error, updateUser } = useUser(userId);
  
  // 4-4. useMemo
  const displayName = useMemo(() => {
    return user ? formatUserName(user) : '';
  }, [user]);
  
  // 4-5. useCallback
  const handleSave = useCallback(async () => {
    try {
      const updatedUser = await updateUser(editForm);
      setIsEditing(false);
      onUserUpdate?.(updatedUser);
      toast.success('更新しました');
    } catch (error) {
      toast.error('更新に失敗しました');
    }
  }, [editForm, updateUser, onUserUpdate]);
  
  // 4-6. useEffect
  useEffect(() => {
    if (user) {
      setEditForm({ name: user.name, email: user.email });
    }
  }, [user]);
  
  // 5. ガード節
  if (isLoading) return <Spinner />;
  if (error) return <div>エラーが発生しました</div>;
  if (!user) return <div>ユーザーが見つかりません</div>;
  
  // 6. メインレンダリング
  return (
    <div className="user-profile">
      <h1>{displayName}</h1>
      {/* その他のJSX */}
    </div>
  );
}
```

## 11. チェックリスト

開発時に確認すべきポイント：

### 構造
- [ ] Import順序は適切か
- [ ] 型定義は完備されているか
- [ ] フックの順序は正しいか
- [ ] 早期returnは適切に配置されているか

### パフォーマンス
- [ ] 不要な再レンダリングは発生していないか
- [ ] useMemo/useCallbackは適切に使用されているか
- [ ] useEffectの依存配列は正しいか

### 保守性
- [ ] 命名規則に従っているか
- [ ] コンポーネントの責務は明確か
- [ ] エラーハンドリングは適切か

このガイドに従うことで、読みやすく保守しやすいReactコンポーネントを作成できます。