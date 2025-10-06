# Stripe設定手順

## 現在の状況
- プロフィール編集は正常に動作
- Stripeアカウント作成で500エラーが発生
- 原因: ダミーキーを使用しているため

## 解決手順

### 1. Stripeアカウント作成
1. [Stripe](https://stripe.com)にアクセス
2. アカウント作成（無料）
3. テストモードに切り替え

### 2. APIキー取得
1. [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)にアクセス
2. 以下のキーをコピー：
   - **Publishable key** (pk_test_...で始まる)
   - **Secret key** (sk_test_...で始まる)

### 3. 設定ファイル更新
`mvp_project/settings.py`の以下の部分を実際のキーに置き換え：

```python
# 現在（ダミーキー）
STRIPE_PUBLISHABLE_KEY = 'pk_test_51234567890abcdef'
STRIPE_SECRET_KEY = 'sk_test_51234567890abcdef'

# 実際のキーに変更（例）
STRIPE_PUBLISHABLE_KEY = 'pk_test_51AbC123...実際のキー'
STRIPE_SECRET_KEY = 'sk_test_51XyZ789...実際のキー'
```

### 4. サーバー再起動
```bash
# バックエンドサーバーを再起動
python manage.py runserver
```

### 5. テスト
1. プロフィールページで「Stripeアカウントを作成」をクリック
2. Stripeのオンボーディングページにリダイレクトされる
3. テスト用情報を入力：
   - **カード番号**: 4242424242424242
   - **有効期限**: 12/25
   - **CVC**: 123

## 期待される動作
- 「Stripeアカウントを作成」→ Stripeオンボーディングページ
- アカウント作成完了後 → 「登録完了」表示
- 投稿者: 報酬支払い用アカウント
- 提案者: 報酬受取・出金用アカウント

## トラブルシューティング
- 500エラー: キーが正しく設定されていない
- リダイレクトしない: ネットワークエラー
- オンボーディングでエラー: テストキーが期限切れ
