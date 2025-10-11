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

# テスト用エンドポイント：スケジューラーを手動実行（通常の7日条件）
@app.route("/test/scheduler", methods=['GET'])
def test_scheduler():
    """スケジューラーのリマインダー処理を手動実行（テスト用）"""
    from scheduler import send_weekly_reminder
    from flask import jsonify
    
    try:
        print("手動でスケジューラーを実行します...")
        send_weekly_reminder()
        return jsonify({
            "status": "success",
            "message": "スケジューラーを手動実行しました"
        })
    except Exception as e:
        print(f"スケジューラー実行エラー: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# テスト用エンドポイント：条件なしで全ユーザーに送信
@app.route("/test/send-now", methods=['GET'])
def test_send_now():
    """条件なしで全ユーザーにリマインダーを送信（テスト専用）"""
    from flask import jsonify
    from db_models import get_db_session, User, Company
    from config import get_line_client
    from linebot.v3.messaging import TextMessage, QuickReply, QuickReplyItem, MessageAction
    from utils import send_line_message
    
    try:
        results = []
        
        for bot_id in BOT_CONFIGS:
            api = get_line_client(bot_id)
            
            with get_db_session(DATABASE_URL) as session:
                company = session.query(Company).filter_by(bot_id=bot_id).first()
                if not company:
                    continue
                
                # 条件なし：この企業の全ユーザーに送信
                users = session.query(User).filter(
                    User.company_id == company.id,
                    User.program_sent_date != None,
                    User.question_sent == False
                ).all()
                
                for user in users:
                    quick_reply = QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="0回", text="0回")),
                            QuickReplyItem(action=MessageAction(label="1~3回", text="1~3回")),
                            QuickReplyItem(action=MessageAction(label="4~7回", text="4~7回"))
                        ]
                    )
                    
                    message_text = f"{user.username}さん、{company.name}の足健康プログラムからお知らせです。この1週間で運動は何回できましたか？0〜7回でご回答ください。"
                    message = TextMessage(text=message_text, quick_reply=quick_reply)
                    
                    success = send_line_message(api, "push", user.line_user_id, [message], user, session, bot_id)
                    
                    if success:
                        user.question_sent = True
                        session.commit()
                        results.append(f"送信成功: {user.line_user_id}")
                    else:
                        results.append(f"送信失敗: {user.line_user_id}")
        
        return jsonify({
            "status": "success",
            "message": "テスト送信完了",
            "results": results
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ヘルスチェック用エンドポイント
@app.route("/health", methods=['GET'])
def health_check():
    """ヘルスチェック"""
    from flask import jsonify
    return jsonify({
        "status": "ok",
        "companies": len(BOT_CONFIGS)
    })

# 運動履歴確認用エンドポイント
@app.route("/history/<bot_id>", methods=['GET'])
def get_exercise_history(bot_id):
    """企業の運動履歴を取得"""
    from flask import jsonify, request
    from db_models import get_db_session, User, Company, ExerciseHistory
    from sqlalchemy import func
    
    if bot_id not in BOT_CONFIGS:
        return jsonify({"error": "Invalid bot_id"}), 404
    
    try:
        with get_db_session(DATABASE_URL) as session:
            company = session.query(Company).filter_by(bot_id=bot_id).first()
            if not company:
                return jsonify({"error": "Company not found"}), 404
            
            # クエリパラメータで特定ユーザーの履歴を取得
            user_id = request.args.get('user_id')
            
            if user_id:
                # 特定ユーザーの履歴
                user = session.query(User).filter_by(
                    line_user_id=user_id,
                    company_id=company.id
                ).first()
                
                if not user:
                    return jsonify({"error": "User not found"}), 404
                
                histories = session.query(ExerciseHistory).filter_by(
                    user_id=user.id
                ).order_by(ExerciseHistory.response_date.desc()).all()
                
                result = {
                    "user_id": user.line_user_id,
                    "username": user.username,
                    "foot_check_result": user.foot_check_result,
                    "current_week": user.current_week,
                    "history": [
                        {
                            "date": h.response_date.isoformat(),
                            "response_text": h.response_text,
                            "response_days": h.response_days,
                            "week_number": h.week_number
                        }
                        for h in histories
                    ]
                }
            else:
                # 企業全体の統計
                total_users = session.query(func.count(User.id)).filter_by(
                    company_id=company.id
                ).scalar()
                
                total_responses = session.query(func.count(ExerciseHistory.id)).filter_by(
                    company_id=company.id
                ).scalar()
                
                avg_response_days = session.query(func.avg(ExerciseHistory.response_days)).filter_by(
                    company_id=company.id
                ).scalar()
                
                result = {
                    "company": company.name,
                    "total_users": total_users,
                    "total_responses": total_responses,
                    "average_exercise_days": float(avg_response_days) if avg_response_days else 0
                }
            
            return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
