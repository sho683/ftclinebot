import re
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from linebot.v3.webhooks import FollowEvent, MessageEvent, TextMessageContent
from linebot.v3.messaging import TextMessage, ImageMessage
from db_models import User, get_db_session, Company
from utils import send_line_message, log_message, log_error
from config import get_line_client, get_webhook_handler, BOT_CONFIGS, DATABASE_URL

# 各bot_idに対応するハンドラを保持する辞書
handlers = {}

# 各bot_idに対応するLINE APIクライアントを保持する辞書
line_clients = {}

def setup_handlers():
    """全てのBot用のハンドラーをセットアップする"""
    global handlers, line_clients
    
    for bot_id in BOT_CONFIGS:
        # ハンドラーとクライアントを取得
        handler = get_webhook_handler(bot_id)
        line_client = get_line_client(bot_id)
        
        if not handler or not line_client:
            print(f"Failed to setup handler for bot_id: {bot_id}")
            continue
        
        # 各bot_id用の別々のハンドラー関数を作成するためのファクトリー関数
        def create_handlers(current_bot_id):
            @handler.add(FollowEvent)
            def handle_follow(event):
                handle_follow_event(event, current_bot_id)
                
            @handler.add(MessageEvent)
            def handle_message(event):
                if isinstance(event.message, TextMessageContent):
                    handle_message_event(event, current_bot_id)
        
        # ここで各botに対するハンドラを生成
        create_handlers(bot_id)
        
        # 辞書に保存
        handlers[bot_id] = handler
        line_clients[bot_id] = line_client
        
        print(f"Set up handler for bot_id: {bot_id}")
    
    return handlers

def get_handler(bot_id):
    """指定されたbot_idのハンドラーを取得"""
    if bot_id not in handlers:
        handlers[bot_id] = get_webhook_handler(bot_id)
    return handlers[bot_id]

def get_api(bot_id):
    """指定されたbot_idのLINE APIクライアントを取得"""
    if bot_id not in line_clients:
        line_clients[bot_id] = get_line_client(bot_id)
    return line_clients[bot_id]

def handle_follow_event(event, bot_id):
    """友だち追加イベントの処理"""
    print(f"Processing follow event for bot_id: {bot_id}, user: {event.source.user_id}")
    with get_db_session(DATABASE_URL) as session:
        try:
            user_id = event.source.user_id
            api = get_api(bot_id)  # 重要：該当botのAPIクライアントを使用
            
            # 企業情報を取得
            company = session.query(Company).filter_by(bot_id=bot_id).first()
            if not company:
                print(f"Company not found for bot_id: {bot_id}")
                return
            
            # ユーザープロフィールの取得
            try:
                profile = api.get_profile(user_id=user_id)
                username = profile.display_name
            except Exception as e:
                print(f"Failed to get user profile: {e}")
                username = "Unknown User"

            # この企業とLINE IDの組み合わせでユーザーを検索
            user = session.query(User).filter_by(
                line_user_id=user_id,
                company_id=company.id
            ).first()
            
            if not user:
                # 新規ユーザー登録
                user = User(
                    line_user_id=user_id,
                    username=username,
                    company_id=company.id
                )
                session.add(user)
                session.commit()
                log_message(session, user, "system", f"新規ユーザー登録: {username}")

                # ユーザー名と企業名を含むメッセージを送信
                message = f"{username}さん、{company.name}の足健康プログラムへようこそ！\n足の健康チェックを始めましょう。"
                send_line_message(api, "reply", event.reply_token, [TextMessage(text=message)], user, session, bot_id)
                log_message(session, user, "sent", "ウェルカムメッセージ送信")
            else:
                log_message(session, user, "system", f"既存ユーザー: {username}")
                # 既存ユーザーの場合もウェルカムメッセージを送信
                message = f"{username}さん、またお会いできて嬉しいです！\n{company.name}の足健康プログラムを再開しましょう。"
                send_line_message(api, "reply", event.reply_token, [TextMessage(text=message)], user, session, bot_id)

        except Exception as e:
            log_error("handle_follow", e, None, session)

def handle_message_event(event, bot_id):
    """メッセージイベントの処理"""
    print(f"Processing message event for bot_id: {bot_id}, event: {event.type}, user: {event.source.user_id}")
    with get_db_session(DATABASE_URL) as session:
        try:
            user_id = event.source.user_id
            text = event.message.text.strip()
            api = get_api(bot_id)  # 重要：該当botのAPIクライアントを使用

            # 企業情報を取得
            company = session.query(Company).filter_by(bot_id=bot_id).first()
            if not company:
                print(f"Company not found for bot_id: {bot_id}")
                return

            # この企業とLINE IDの組み合わせでユーザーを検索
            user = session.query(User).filter_by(
                line_user_id=user_id,
                company_id=company.id
            ).first()
            
            if not user:
                # 新規ユーザー作成
                try:
                    profile = api.get_profile(user_id=user_id)
                    username = profile.display_name
                except Exception as e:
                    print(f"Failed to get user profile: {e}")
                    username = "Unknown User"
                    
                user = User(
                    line_user_id=user_id,
                    username=username,
                    company_id=company.id
                )
                session.add(user)
                session.commit()
                log_message(session, user, "system", "新規ユーザー登録（メッセージ受信時）")

            # A〜Dのパターンマッチング（大文字小文字、全角半角に対応）
            foot_check_pattern = re.compile(r'^[aAａＡbBｂＢcCｃＣdDｄＤ]$')
            if foot_check_pattern.match(text):
                # 足健診結果の処理
                process_foot_check_result(event, text, user, company, api, session, bot_id)
            elif "回" in text or (text.isdigit() and 0 <= int(text) <= 7):
                # 運動日数の処理（クイックリプライの「0回」「1~3回」「4~7回」または数値）
                process_exercise_days(event, text, user, company, api, session, bot_id)
            else:
                # その他のメッセージ処理
                process_other_message(event, text, user, company, api, session, bot_id)

        except Exception as e:
            log_error("handle_message", e, None, session)

def process_foot_check_result(event, text, user, company, api, session, bot_id):
    """足健診結果の処理"""
    # 入力された文字を大文字の半角に正規化
    normalized_result = text.upper()
    if normalized_result in ['Ａ', 'Ｂ', 'Ｃ', 'Ｄ']:
        normalized_result = normalized_result.translate(str.maketrans('ＡＢＣＤ', 'ABCD'))
    
    # プロフィール情報を直接取得 - ここを追加
    try:
        profile = api.get_profile(user_id=user.line_user_id)
        username = profile.display_name
        # ユーザー名を更新
        if username and username != user.username:
            user.username = username
            session.commit()
            print(f"ユーザー名を更新しました: {username}")
    except Exception as e:
        print(f"プロフィール取得エラー: {e}")
        username = user.username  # データベースの既存値を使用
    
    # ユーザー名のフォールバック
    display_name = username if username else "ゲスト"
    
    user.foot_check_result = normalized_result
    user.last_program_type = "initial"
    user.current_week = 0  # 初回登録は0週目
    user.question_sent = False
    user.program_sent_date = datetime.utcnow()  # 日付を更新
    session.commit()

    log_message(session, user, "received", f"足健診結果: {normalized_result}")
    log_message(session, user, "system", f"足健診結果を{normalized_result}に更新、0週目に設定")

    # A/B/C/D共通のメッセージ（初回登録時は動画を送らない）
    message = f"{display_name}さん、足健診結果の入力ありがとうございます！1週間後に新しい運動メニューを配信しますので、今日教わった内容を継続しましょう！"
    success = send_line_message(
        api, "reply", event.reply_token,
        [TextMessage(text=message)],
        user, session, bot_id
    )
    if success:
        log_message(session, user, "sent", "足健診結果受付メッセージ送信")

def process_exercise_days(event, text, user, company, api, session, bot_id):
    """運動日数の処理（クイックリプライからの回答）"""
    from config import (EXERCISE_VIDEO_URLS_AB, EXERCISE_VIDEO_URLS_CD, 
                        EXERCISE_THUMBNAIL_URLS_AB, EXERCISE_THUMBNAIL_URLS_CD,
                        EXERCISE_IMAGE_URLS_AB, EXERCISE_IMAGE_URLS_CD)
    from utils import create_exercise_video_flex_message
    
    # プロフィール情報を直接取得
    try:
        profile = api.get_profile(user_id=user.line_user_id)
        username = profile.display_name
        # ユーザー名を更新
        if username and username != user.username:
            user.username = username
            session.commit()
            print(f"ユーザー名を更新しました: {username}")
    except Exception as e:
        print(f"プロフィール取得エラー: {e}")
        username = user.username  # データベースの既存値を使用
    
    # ユーザー名のフォールバック
    display_name = username if username else "ゲスト"
    
    # 足健診結果が未設定の場合は先に入力を促す
    if not user.foot_check_result:
        message = f"{display_name}さん、先に足の健康チェック結果を教えてください。A、B、C、Dのいずれかで回答してください。"
        success = send_line_message(
            api, "reply", event.reply_token,
            [TextMessage(text=message)],
            user, session, bot_id
        )
        if success:
            log_message(session, user, "sent", "足健診結果入力リクエスト")
        return  # ここで処理を終了
    
    # クイックリプライの選択肢を判定
    # 「0回」「1~3回」「4~7回」のテキストから数値を抽出
    if "0" in text or text == "0回":
        days = 0
        response_message = f"{display_name}さん、大丈夫です。次週は1回だけで構いません。一緒に頑張りましょう。"
    elif "1" in text or "3" in text:  # 「1~3回」または「1-3回」
        days = 2  # 中央値として保存
        response_message = f"{display_name}さん、その調子です。今週も一緒に頑張りましょう。"
    elif "4" in text or "7" in text:  # 「4~7回」または「4-7回」
        days = 5  # 中央値として保存
        response_message = f"{display_name}さん、素晴らしいですね！その調子で継続しましょう。"
    else:
        # 想定外のテキスト（念のため）
        log_message(session, user, "error", f"想定外の運動回数: {text}")
        return
    
    # 週番号の取得と更新
    current_week = user.current_week if user.current_week else 0
    
    # 0週目（初回）なら1週目に進める
    if current_week == 0:
        current_week = 1
    
    # データベースを更新
    user.last_response_days = days
    user.question_sent = False  # 質問に回答したのでフラグをリセット
    user.program_sent_date = datetime.utcnow()  # 日付を更新
    user.last_program_type = "continued"
    
    log_message(session, user, "received", f"運動回数: {text}")
    log_message(session, user, "system", f"運動日数を{days}に更新、{current_week}週目の動画を送信")

    # 評価結果に応じて動画セットを選択（A/BとC/Dは同じ動画）
    if user.foot_check_result in ['A', 'B']:
        video_urls = EXERCISE_VIDEO_URLS_AB
        thumbnail_urls = EXERCISE_THUMBNAIL_URLS_AB
        image_urls = EXERCISE_IMAGE_URLS_AB
    else:  # C または D
        video_urls = EXERCISE_VIDEO_URLS_CD
        thumbnail_urls = EXERCISE_THUMBNAIL_URLS_CD
        image_urls = EXERCISE_IMAGE_URLS_CD
    
    # 週番号に応じた動画・画像を取得（インデックスは0始まりなのでcurrent_week - 1）
    video_url = video_urls[current_week - 1]
    thumbnail_url = thumbnail_urls[current_week - 1]
    image_url = image_urls[current_week - 1]
    
    # デバッグ用ログ
    print(f"使用するURL - 動画: {video_url}")
    print(f"使用するURL - サムネイル: {thumbnail_url}")
    print(f"使用するURL - 静止画: {image_url}")
    print(f"静止画URLがHTTPSか: {image_url.startswith('https://')}")
    
    # Flex Messageを生成
    flex_message = create_exercise_video_flex_message(video_url, thumbnail_url)
    
    # メッセージ、動画、静止画を送信
    success = send_line_message(
        api, "reply", event.reply_token,
        [
            TextMessage(text=response_message), 
            flex_message,
            ImageMessage(original_content_url=image_url, preview_image_url=image_url)
        ],
        user, session, bot_id
    )
    if success:
        log_message(session, user, "sent", f"運動メニュー動画送信（{current_week}週目、{text}）")
        
        # 運動履歴を保存
        from db_models import ExerciseHistory
        history = ExerciseHistory(
            user_id=user.id,
            response_days=days,
            response_text=text,
            week_number=current_week,
            foot_check_result=user.foot_check_result,
            company_id=user.company_id
        )
        session.add(history)
        
        # 次回の週番号を更新（12週目の次は1週目に戻る）
        next_week = (current_week % 12) + 1
        user.current_week = next_week
        session.commit()
        print(f"週番号を{current_week}から{next_week}に更新しました")
        print(f"運動履歴を保存しました: {days}回（{text}）")

def process_other_message(event, text, user, company, api, session, bot_id):
    """その他のメッセージ処理"""
    # 一方的なメッセージのログ記録
    log_message(session, user, "received", f"一方的なメッセージ: {text}")
    
    # プロフィール情報を取得してユーザー名を更新
    try:
        profile = api.get_profile(user_id=user.line_user_id)
        display_name = profile.display_name
        if display_name and display_name != user.username:
            user.username = display_name
            session.commit()
    except Exception as e:
        print(f"プロフィール取得エラー: {e}")
        display_name = user.username  # データベースの既存値を使用
    
    # 汎用応答メッセージ
    message = f"{display_name}さん、申し訳ありませんが、{company.name}の足健康プログラムは足健診結果に基づいた運動プログラムの提供と、運動の継続状況の確認のみに対応しています。\n\n個別のご質問やご相談には対応できませんので、ご了承ください。\n\n足健診結果はA〜D（大文字小文字、全角半角どちらでも可）、または運動日数は1〜7の数字で入力してください。\n\n運動プログラムの継続状況については、1週間ごとにご連絡いたします。"
    success = send_line_message(
        api, "reply", event.reply_token,
        [TextMessage(text=message)],
        user, session, bot_id
    )
    if success:
        log_message(session, user, "sent", "個別対応不可の案内メッセージ送信")

# 初期化時にハンドラーをセットアップ
setup_handlers()
