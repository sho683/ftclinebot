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
        "name": os.getenv("COMPANY1_NAME", "Company 1")
    }
    print(f"company1 の設定を読み込みました: {BOT_CONFIGS['company1']['name']}")

# company2 があれば追加
if os.getenv("COMPANY2_CHANNEL_SECRET") and os.getenv("COMPANY2_ACCESS_TOKEN"):
    BOT_CONFIGS["company2"] = {
        "channel_secret": os.getenv("COMPANY2_CHANNEL_SECRET"),
        "access_token": os.getenv("COMPANY2_ACCESS_TOKEN"),
        "name": os.getenv("COMPANY2_NAME", "Company 2")
    }
    print(f"company2 の設定を読み込みました: {BOT_CONFIGS['company2']['name']}")

# company3 があれば追加
if os.getenv("COMPANY3_CHANNEL_SECRET") and os.getenv("COMPANY3_ACCESS_TOKEN"):
    BOT_CONFIGS["company3"] = {
        "channel_secret": os.getenv("COMPANY3_CHANNEL_SECRET"),
        "access_token": os.getenv("COMPANY3_ACCESS_TOKEN"),
        "name": os.getenv("COMPANY3_NAME", "Company 3")
    }
    print(f"company3 の設定を読み込みました: {BOT_CONFIGS['company3']['name']}")

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

# 運動メニュー動画URL（YouTube）- 12週分×2セット
# 環境変数から読み込み、なければダミーURLを使用
# A/B評価用（同じ動画）
EXERCISE_VIDEO_URLS_AB = [
    os.getenv("EXERCISE_VIDEO_AB_WEEK1", "https://www.youtube.com/watch?v=DUMMY_AB_W1"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK2", "https://www.youtube.com/watch?v=DUMMY_AB_W2"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK3", "https://www.youtube.com/watch?v=DUMMY_AB_W3"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK4", "https://www.youtube.com/watch?v=DUMMY_AB_W4"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK5", "https://www.youtube.com/watch?v=DUMMY_AB_W5"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK6", "https://www.youtube.com/watch?v=DUMMY_AB_W6"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK7", "https://www.youtube.com/watch?v=DUMMY_AB_W7"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK8", "https://www.youtube.com/watch?v=DUMMY_AB_W8"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK9", "https://www.youtube.com/watch?v=DUMMY_AB_W9"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK10", "https://www.youtube.com/watch?v=DUMMY_AB_W10"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK11", "https://www.youtube.com/watch?v=DUMMY_AB_W11"),
    os.getenv("EXERCISE_VIDEO_AB_WEEK12", "https://www.youtube.com/watch?v=DUMMY_AB_W12"),
]

# C/D評価用（同じ動画）
EXERCISE_VIDEO_URLS_CD = [
    os.getenv("EXERCISE_VIDEO_CD_WEEK1", "https://www.youtube.com/watch?v=DUMMY_CD_W1"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK2", "https://www.youtube.com/watch?v=DUMMY_CD_W2"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK3", "https://www.youtube.com/watch?v=DUMMY_CD_W3"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK4", "https://www.youtube.com/watch?v=DUMMY_CD_W4"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK5", "https://www.youtube.com/watch?v=DUMMY_CD_W5"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK6", "https://www.youtube.com/watch?v=DUMMY_CD_W6"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK7", "https://www.youtube.com/watch?v=DUMMY_CD_W7"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK8", "https://www.youtube.com/watch?v=DUMMY_CD_W8"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK9", "https://www.youtube.com/watch?v=DUMMY_CD_W9"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK10", "https://www.youtube.com/watch?v=DUMMY_CD_W10"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK11", "https://www.youtube.com/watch?v=DUMMY_CD_W11"),
    os.getenv("EXERCISE_VIDEO_CD_WEEK12", "https://www.youtube.com/watch?v=DUMMY_CD_W12"),
]

# 運動メニュー動画のサムネイル画像URL - 12週分×2セット
# A/B評価用
EXERCISE_THUMBNAIL_URLS_AB = [
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK1", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W1.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK2", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W2.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK3", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W3.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK4", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W4.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK5", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W5.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK6", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W6.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK7", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W7.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK8", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W8.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK9", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W9.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK10", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W10.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK11", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W11.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_AB_WEEK12", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_AB_W12.jpg"),
]

# C/D評価用
EXERCISE_THUMBNAIL_URLS_CD = [
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK1", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W1.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK2", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W2.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK3", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W3.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK4", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W4.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK5", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W5.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK6", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W6.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK7", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W7.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK8", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W8.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK9", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W9.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK10", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W10.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK11", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W11.jpg"),
    os.getenv("EXERCISE_THUMBNAIL_CD_WEEK12", "https://jp-hc.com/wordpress/wp-content/uploads/2025/05/exercises_CD_W12.jpg"),
]

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
