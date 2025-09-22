# MVP Project

DjangoとNext.jsを使用したフルスタックウェブアプリケーションのプロジェクトです。

## プロジェクト構成

```
mvp_project/
├── mvp_project/          # Djangoプロジェクト設定
│   ├── __init__.py
│   ├── settings.py       # Django設定（CORS設定済み）
│   ├── urls.py
│   └── wsgi.py
├── mvp_app/              # Djangoアプリケーション
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   └── migrations/
├── frontend/             # Next.jsフロントエンド
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── next.config.js
├── venv/                 # Python仮想環境
├── requirements.txt      # Python依存関係
└── README.md
```

## セットアップ手順

### 1. 仮想環境のアクティベート

```bash
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

### 2. Djangoサーバーの起動

```bash
# データベースマイグレーション
python manage.py migrate

# 開発サーバー起動（ポート8000）
python manage.py runserver
```

### 3. Next.jsフロントエンドの起動

```bash
# frontendディレクトリに移動
cd frontend

# 依存関係のインストール（初回のみ）
npm install

# 開発サーバー起動（ポート3000）
npm run dev
```

## アクセス

- **フロントエンド**: http://localhost:3000
- **Django API**: http://localhost:8000
- **Django管理画面**: http://localhost:8000/admin

## 技術スタック

### バックエンド
- **Django 5.2.6**: Webフレームワーク
- **Django REST Framework**: API構築
- **django-cors-headers**: CORS設定

### フロントエンド
- **Next.js 15**: Reactフレームワーク
- **TypeScript**: 型安全性
- **Tailwind CSS**: スタイリング
- **ESLint**: コード品質管理

## 開発の流れ

1. DjangoでAPIエンドポイントを作成
2. Next.jsでフロントエンドコンポーネントを作成
3. APIとフロントエンドを連携
4. テストとデバッグ

## 注意事項

- 本設定は開発環境用です。本番環境では適切なセキュリティ設定を行ってください
- CORS設定は開発環境では全許可になっています

