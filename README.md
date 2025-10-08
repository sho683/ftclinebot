# LINE Bot - 足の健康管理アプリケーション

足の健康状態を判定し、適切な運動プログラムを提供するLINE Botアプリケーション。

## 機能

- 足の健康状態チェック (A/B/C/D)
- 足の状態に応じた運動プログラムの提供
- 週次リマインダーによる継続サポート
- 運動継続状況の追跡

## 技術スタック

- Python 3.9+
- Flask
- LINE Messaging API
- SQLAlchemy (PostgreSQL)
- APScheduler

## 本番環境へのデプロイ手順

### 前提条件

- LINE Developersアカウントとチャネルの作成
- PostgreSQLデータベースの準備
- Pythonが利用可能なホスティングサービス（Render.com, Heroku, AWS, GCPなど）

### 1. 環境変数の設定

`.env.example`ファイルをコピーして`.env`ファイルを作成し、必要な環境変数を設定します。

```bash
cp .env.example .env
```

以下の環境変数を設定してください：

- `LINE_ACCESS_TOKEN`: LINE Developer Consoleで取得したアクセストークン
- `LINE_CHANNEL_SECRET`: LINE Developer Consoleで取得したチャネルシークレット
- `DATABASE_URL`: PostgreSQLのデータベース接続URL
- その他の設定パラメータ（必要に応じて）

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. データベースのマイグレーション

アプリケーション初回起動時に自動的にマイグレーションが実行されます。手動で実行したい場合は以下のコマンドを使用します。

```bash
python -c "from db_models import run_migrations; run_migrations('your_database_url_here')"
```

### 4. アプリケーションの起動

```bash
gunicorn main:app
```

または

```bash
python main.py
```

### 5. LINE WebhookのURL設定

LINE Developer Consoleで、Webhook URLを以下のように設定します：

```
https://your-domain.com/callback
```

### セキュリティ上の注意点

- 本番環境では必ず環境変数を使用してください
- データベース接続文字列やLINE APIトークンは公開リポジトリにコミットしないでください
- 本番環境ではデバッグモードを無効にしてください (`DEBUG=false`)

## 開発環境のセットアップ

1. リポジトリをクローン
2. 環境変数ファイル（.env）を作成
3. 仮想環境を作成してアクティベート
4. 依存パッケージをインストール
5. 開発サーバーを起動

```bash
git clone [リポジトリURL]
cd [リポジトリ名]
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Webhookのテスト

開発環境でテストするには、ngrokなどのツールを使用して一時的な公開URLを取得します：

```bash
ngrok http 10000
```

取得したURLをLINE Developer ConsoleのWebhook URLに設定します。

## メンテナンス

### ログ確認

アプリケーションログを定期的に確認して、エラーや警告を監視しましょう。

### スケジューラーの状態確認

スケジューラーが正常に動作していることを確認します：

```
curl https://your-domain.com/healthcheck
```

### データベースのバックアップ

定期的にデータベースのバックアップを取得することをお勧めします。

## トラブルシューティング

- **Webhook接続エラー**: LINE Developer ConsoleでWebhook URLが正しく設定されているか確認
- **データベース接続エラー**: DATABASE_URLが正しいか、ネットワーク接続に問題がないか確認
- **スケジューラーが動作しない**: アプリケーションログを確認し、必要に応じて手動でリマインダー処理を実行