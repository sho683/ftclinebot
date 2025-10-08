from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from linebot.v3.messaging import TextMessage, QuickReply, QuickReplyItem, MessageAction
from db_models import get_db_session, User, Company
from sqlalchemy import text
from utils import send_line_message, log_message, log_error
from config import get_line_client, BOT_CONFIGS, DATABASE_URL

def send_weekly_reminder():
    """ユーザーごとに個別のリマインダーを送信する関数（定期チェック）"""
    print("Reminder check started at:", datetime.utcnow())
    
    # 各企業ごとに処理
    for bot_id, config in BOT_CONFIGS.items():
        send_company_reminders(bot_id)

def send_company_reminders(bot_id):
    """指定された企業のユーザーにリマインダーを送信"""
    print(f"Processing reminders for bot_id: {bot_id}")
    api = get_line_client(bot_id)
    
    if not api:
        print(f"Failed to get LINE API client for bot_id: {bot_id}")
        return
    
    with get_db_session(DATABASE_URL) as session:
        try:
            # セッション開始後にステートメントタイムアウトを設定
            try:
                session.execute(text("SET statement_timeout = '30s'"))
                session.commit()
                print("Statement timeout set successfully")
            except Exception as e:
                print(f"Failed to set statement timeout: {e}")
            
            # 企業情報を取得
            company = session.query(Company).filter_by(bot_id=bot_id).first()
            if not company:
                print(f"Company not found for bot_id: {bot_id}")
                return
            
            # 現在時刻から7日前を計算
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)
            
            # この企業に属するユーザーで、最後の回答から7日以上経過したユーザーを抽出
            # question_sent=Falseで重複送信を防ぐ（ユーザーが回答するとFalseにリセットされる）
            users = session.query(User).filter(
                User.company_id == company.id,
                User.program_sent_date != None,
                User.program_sent_date <= seven_days_ago,
                User.question_sent == False  # まだ質問を送っていない
            ).all()
            
            print(f"Found {len(users)} users for company {company.name} to send weekly reminder")
            
            # 各ユーザーにメッセージを送信
            for user in users:
                print(f"Sending to user {user.id}, last program: {user.program_sent_date}, question_sent: {user.question_sent}")
                
                # クイックリプライの選択肢を作成
                quick_reply = QuickReply(
                    items=[
                        QuickReplyItem(
                            action=MessageAction(label="0回", text="0回")
                        ),
                        QuickReplyItem(
                            action=MessageAction(label="1~3回", text="1~3回")
                        ),
                        QuickReplyItem(
                            action=MessageAction(label="4~7回", text="4~7回")
                        )
                    ]
                )
                
                # クイックリプライ付きメッセージ
                message_text = f"{user.username}さん、{company.name}の足健康プログラムからお知らせです。この1週間で運動は何回できましたか？0〜7回でご回答ください。"
                message = TextMessage(text=message_text, quick_reply=quick_reply)
                
                success = send_line_message(
                    api, "push", user.line_user_id,
                    [message],
                    user, session, bot_id
                )
                
                if success:
                    # 送信成功したらフラグを立てる
                    user.question_sent = True
                    session.commit()
                    print(f"Updated user {user.line_user_id} status")
                
        except Exception as e:
            log_error(f"send_company_reminders({bot_id})", e, None, session)

def start_scheduler():
    """スケジューラーを起動する関数"""
    print("Starting scheduler...")
    scheduler = BackgroundScheduler()
    
    # 6時間ごとに実行（1日4回チェック）
    # これにより、各ユーザーの回答時刻から正確に7日後にメッセージを送信
    scheduler.add_job(
        send_weekly_reminder, 
        'interval', 
        hours=6,
        id='individual_reminder'
    )
    
    scheduler.start()
    print("Individual reminder scheduler started (checks every 6 hours)")
