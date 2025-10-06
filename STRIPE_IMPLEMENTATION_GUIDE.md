# Stripe実装ガイド

## 1. 現在の実装（テスト用）

### Customer実装（Connect不要）
- 投稿者と提案者が同じプラットフォーム内で決済
- プラットフォームが決済を管理
- 実際の外部送金は不可

## 2. 本番環境での実装（Connect使用）

### Connect実装（投稿者→提案者の直接送金）

#### 投稿者側（支払い）
```python
# 投稿者のウォレットから提案者へ送金
transfer = stripe.Transfer.create(
    amount=amount_cents,
    currency='jpy',
    destination=proposer_stripe_account_id,  # 提案者のConnectアカウント
    metadata={
        'challenge_id': challenge_id,
        'proposal_id': proposal_id,
    }
)
```

#### 提案者側（受取）
```python
# 提案者のConnectアカウント作成
account = stripe.Account.create(
    type='express',
    country='JP',
    email=proposer.email,
)
```

## 3. APIキー管理

### 開発環境
```python
# settings.py
STRIPE_SECRET_KEY = 'sk_test_...'  # 開発者用テストキー
```

### 本番環境
```python
# settings.py
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')  # 環境変数
```

### 環境変数の設定例
```bash
# .env ファイル
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## 4. 利用者への影響

### 利用者（投稿者・提案者）
- **APIキー入力不要**
- プラットフォーム経由でStripe機能を利用
- 投稿者：クレジットカード決済
- 提案者：Connectアカウント作成（銀行口座登録）

### サービス提供者（あなた）
- Stripeアカウント作成・管理
- APIキーの設定・管理
- 手数料の設定

## 5. 実装の選択

### 現在（テスト用）
- ✅ 簡単に実装可能
- ✅ Connect不要
- ❌ 実際の送金不可

### 本番環境（推奨）
- ✅ 実際の送金可能
- ✅ 投稿者→提案者の直接送金
- ❌ Connect設定必要
- ❌ 複雑な実装

## 6. 次のステップ

1. **現在の実装でテスト完了**
2. **本番環境ではConnect実装に移行**
3. **環境変数でAPIキー管理**
4. **利用者はAPIキー入力不要**
