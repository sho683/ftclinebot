import os
from flask import Flask, request, abort
from line_handlers import get_handler
from scheduler import start_scheduler
from db_models import run_migrations, ensure_companies_exist
from config import DATABASE_URL, BOT_CONFIGS

# Flask アプリ作成
app = Flask(__name__)

# データベース初期化とマイグレーション
try:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set.")
    engine = run_migrations(DATABASE_URL)
    print("✅ データベースマイグレーション完了")
    
    # 企業レコードを確認・作成
    ensure_companies_exist()
    print("✅ 企業レコードの確認・作成完了")
except Exception as e:
    print(f"❌ データベース初期化失敗: {e}")
    # サーバー起動は継続

# スケジューラーを起動
start_scheduler()
print("✅ スケジューラー起動完了")

# 環境確認ログ
import flask
print(f"✅ Flask Version: {flask.__version__}")
print(f"✅ 設定済み企業数: {len(BOT_CONFIGS)}")

@app.route("/callback/<bot_id>", methods=['POST'])
def callback(bot_id):
    """各企業のLINE Bot用Webhookエンドポイント"""
    if bot_id not in BOT_CONFIGS:
        print(f"Unknown bot_id: {bot_id}")
        abort(404)
    
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    print(f"Received webhook for bot_id: {bot_id}, signature: {signature[:10]}...")
    
    handler = get_handler(bot_id)
    if not handler:
        print(f"Failed to get handler for bot_id: {bot_id}")
        abort(500)

    try:
        # ハンドラーでWebhookを処理
        handler.handle(body, signature)
        return 'OK'
    except Exception as e:
        print(f"Webhook error for {bot_id}: {e}")
        abort(400)

# 後方互換性のための従来のエンドポイント（開発時のみ使用推奨）
@app.route("/callback", methods=['POST'])
def legacy_callback():
    """従来のエンドポイント（デフォルトのbot_idを使用）"""
    from config import DEFAULT_BOT_ID, SINGLE_TENANT_MODE
    
    if not SINGLE_TENANT_MODE or not DEFAULT_BOT_ID:
        abort(404)  # シングルテナントモードでない場合は404
    
    return callback(DEFAULT_BOT_ID)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
