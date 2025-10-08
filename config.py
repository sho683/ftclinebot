# config.py
import os
import json
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3 import WebhookHandler
# 個別の環境変数からBOT_CONFIGSを構築
BOT_CONFIGS = {}

# company1 の設定
if os.getenv("COMPANY1_CHANNEL_SECRET") and os.getenv("COMPANY1_ACCESS_TOKEN"):
    BOT_CONFIGS["company1"] = {
        "channel_secret": os.getenv("COMPANY1_CHANNEL_SECRET"),
        "access_token": os.getenv("COMPANY1_ACCESS_TOKEN"),
        "name": os.getenv("COMPANY1_NAME", "池田市足健診")
    }
    print(f"company1 の設定を読み込みました: {BOT_CONFIGS['company1']['name']}")

# company2 があれば追加
if os.getenv("COMPANY2_CHANNEL_SECRET") and os.getenv("COMPANY2_ACCESS_TOKEN"):
    BOT_CONFIGS["company2"] = {
        "channel_secret": os.getenv("COMPANY2_CHANNEL_SECRET"),
        "access_token": os.getenv("COMPANY2_ACCESS_TOKEN"),
        "name": os.getenv("COMPANY2_NAME", "楢葉町足健診")
    }
    print(f"company2 の設定を読み込みました: {BOT_CONFIGS['company2']['name']}")

# JSONで設定されたBOT_CONFIGSがあれば、それも読み込む (バックアップ方法)
if os.getenv("BOT_CONFIGS"):
    try:
        json_configs = json.loads(os.getenv("BOT_CONFIGS", "{}"))
        # 既存の設定を上書きせず、足りない分だけ追加
        for bot_id, config in json_configs.items():
            if bot_id not in BOT_CONFIGS:
                BOT_CONFIGS[bot_id] = config
                print(f"JSON設定から {bot_id} の設定を読み込みました")
    except json.JSONDecodeError as e:
        print(f"BOT_CONFIGSのJSONパースに失敗: {e}")

# データベースURL
DATABASE_URL = os.getenv("DATABASE_URL")

# 運動メニュー動画URL（YouTube）
# 環境変数から読み込み、なければダミーURLを使用
EXERCISE_VIDEO_URLS = {
    "A": os.getenv("EXERCISE_VIDEO_A", "https://www.youtube.com/watch?v=DUMMY_VIDEO_A"),
    "B": os.getenv("EXERCISE_VIDEO_B", "https://www.youtube.com/watch?v=DUMMY_VIDEO_B"),
    "C": os.getenv("EXERCISE_VIDEO_C", "https://www.youtube.com/watch?v=DUMMY_VIDEO_C"),
    "D": os.getenv("EXERCISE_VIDEO_D", "https://www.youtube.com/watch?v=DUMMY_VIDEO_D"),
}

# 運動メニュー動画のサムネイル画像URL
EXERCISE_THUMBNAIL_URLS = {
    "A": os.getenv("EXERCISE_THUMBNAIL_A", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_A.jpg"),
    "B": os.getenv("EXERCISE_THUMBNAIL_B", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_B.jpg"),
    "C": os.getenv("EXERCISE_THUMBNAIL_C", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_C.jpg"),
    "D": os.getenv("EXERCISE_THUMBNAIL_D", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_D.jpg"),
}

# LINE APIクライアントとハンドラーを取得する関数
def get_line_client(bot_id):
    """指定されたBOT IDのLINE MessagingAPIクライアントを取得"""
    if bot_id not in BOT_CONFIGS:
        return None
        
    config = BOT_CONFIGS[bot_id]
    configuration = Configuration(access_token=config["access_token"])
    api_client = ApiClient(configuration)
    return MessagingApi(api_client)

def get_webhook_handler(bot_id):
    """指定されたBOT IDのWebhookハンドラーを取得"""
    if bot_id not in BOT_CONFIGS:
        return None
        
    config = BOT_CONFIGS[bot_id]
    return WebhookHandler(config["channel_secret"])

# デバッグ用のシングルテナントモード（開発時のみ）
SINGLE_TENANT_MODE = os.getenv("SINGLE_TENANT_MODE", "False").lower() == "true"
DEFAULT_BOT_ID = os.getenv("DEFAULT_BOT_ID", "")

# シングルテナントモードの場合は従来の環境変数を使用
if SINGLE_TENANT_MODE:
    LEGACY_CONFIG = {
        DEFAULT_BOT_ID: {
            "channel_secret": os.getenv("LINE_CHANNEL_SECRET", ""),
            "access_token": os.getenv("LINE_ACCESS_TOKEN", ""),
            "name": "デフォルト企業"
        }
    }
    # BOT_CONFIGSが空の場合はレガシー設定を使用
    if not BOT_CONFIGS:
        BOT_CONFIGS = LEGACY_CONFIG
