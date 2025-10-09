# Stripe設定ガイド

## 目次
1. [Stripeアカウント設定](#1-stripeアカウント設定)
2. [APIキーの取得](#2-apiキーの取得)
3. [設定ファイルの更新](#3-設定ファイルの更新)
4. [テスト用カード情報](#4-テスト用カード情報)
5. [トラブルシューティング](#5-トラブルシューティング)

## 1. Stripeアカウント設定

### 1.1 Stripeアカウントの作成
1. [Stripe](https://stripe.com)にアクセスしてアカウントを作成
2. テストモードに切り替え（開発用）

### 1.2 利用者への影響
- **利用者（投稿者・提案者）**: APIキー入力不要
- **サービス提供者**: Stripeアカウント作成・管理、APIキーの設定・管理

## 2. APIキーの取得

### 2.1 キーの取得手順
1. [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)にアクセス
2. 以下のキーをコピー：
   - **Publishable key** (pk_test_...)
   - **Secret key** (sk_test_...)

### 2.2 環境変数の設定例
```bash
# .env ファイル
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## 3. 設定ファイルの更新

### 3.1 Django設定 (`mvp_project/settings.py`)
```python
# Stripe設定（テストモード）
STRIPE_PUBLISHABLE_KEY = 'pk_test_your_actual_publishable_key_here'  # 実際のキーに置き換え
STRIPE_SECRET_KEY = 'sk_test_your_actual_secret_key_here'            # 実際のキーに置き換え
STRIPE_WEBHOOK_SECRET = 'whsec_your_actual_webhook_secret_here'      # 実際のキーに置き換え
```

### 3.2 Next.js設定 (環境変数)
`.env.local`ファイルを作成：
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 3.3 サーバー再起動
```bash
# バックエンドサーバーを再起動
python manage.py runserver
```

## 4. テスト用カード情報

### 4.1 成功するカード
- **カード番号**: 4242 4242 4242 4242
- **有効期限**: 任意の未来の日付
- **CVC**: 任意の3桁
- **郵便番号**: 任意の番号

### 4.2 失敗するカード
- **カード番号**: 4000 0000 0000 0002 (Declined)
- **カード番号**: 4000 0000 0000 9995 (Insufficient funds)

## 5. トラブルシューティング

### 5.1 500エラー
- **原因**: キーが正しく設定されていない
- **解決**: `mvp_project/settings.py`のキーを実際のStripeキーに更新

### 5.2 リダイレクトしない
- **原因**: ネットワークエラー
- **解決**: サーバーが起動しているか確認

### 5.3 オンボーディングでエラー
- **原因**: テストキーが期限切れ
- **解決**: 新しいテストキーを取得

## 6. 実装の選択

### 6.1 現在（テスト用）
- ✅ 簡単に実装可能
- ✅ Connect不要
- ❌ 実際の送金不可

### 6.2 本番環境（推奨）
- ✅ 実際の送金可能
- ✅ 投稿者→提案者の直接送金
- ❌ Connect設定必要
- ❌ 複雑な実装

## 7. 次のステップ

1. **現在の実装でテスト完了**
2. **本番環境ではConnect実装に移行**
3. **環境変数でAPIキー管理**
4. **利用者はAPIキー入力不要**
