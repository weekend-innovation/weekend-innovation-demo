# Stripe設定ガイド

## 1. Stripeアカウントの作成
1. [Stripe](https://stripe.com)にアクセスしてアカウントを作成
2. テストモードに切り替え（開発用）

## 2. APIキーの取得
1. [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)にアクセス
2. 以下のキーをコピー：
   - **Publishable key** (pk_test_...)
   - **Secret key** (sk_test_...)

## 3. 設定ファイルの更新

### Django設定 (`mvp_project/settings.py`)
```python
# Stripe設定（テストモード）
STRIPE_PUBLISHABLE_KEY = 'pk_test_your_actual_publishable_key_here'  # 実際のキーに置き換え
STRIPE_SECRET_KEY = 'sk_test_your_actual_secret_key_here'            # 実際のキーに置き換え
STRIPE_WEBHOOK_SECRET = 'whsec_your_actual_webhook_secret_here'      # 実際のキーに置き換え
```

### Next.js設定 (環境変数)
`.env.local`ファイルを作成：
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 4. テスト用カード情報

### 成功するカード
- **カード番号**: 4242 4242 4242 4242
- **有効期限**: 任意の未来の日付
- **CVC**: 任意の3桁
- **郵便番号**: 任意の番号

### 失敗するカード
- **カード番号**: 4000 0000 0000 0002 (Declined)
- **カード番号**: 4000 0000 0000 9995 (Insufficient funds)

## 5. 機能テスト

### 投稿者ユーザー
1. プロフィールで「Stripeアカウントを作成」
2. Stripeのオンボーディング画面で情報入力
3. ウォレットで入金テスト

### 提案者ユーザー
1. プロフィールで「Stripeアカウントを作成」
2. Stripeのオンボーディング画面で情報入力
3. ウォレットで出金テスト

## 6. 本番環境への移行
1. Stripe Dashboardでライブモードに切り替え
2. ライブ用のAPIキーを取得
3. 設定ファイルをライブキーに更新
4. Webhookエンドポイントを設定
