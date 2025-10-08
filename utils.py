# utils.py
import time
from requests.exceptions import RequestException, ConnectionError, Timeout
from urllib3.exceptions import ProtocolError, HTTPError
import socket
from linebot.v3.messaging import ReplyMessageRequest, PushMessageRequest
from sqlalchemy.exc import SQLAlchemyError
from db_models import MessageLog

# bot_idごとに別々のreply_token記録を保持する辞書
used_reply_tokens = {}

def send_line_message(api, message_type, identifier, messages, user=None, session=None, bot_id=None):
    """
    LINE APIへのメッセージ送信関数（汎用）
    :param api: MessagingApiオブジェクト
    :param message_type: "reply" または "push"
    :param identifier: reply_token または user_id
    :param messages: 送信するメッセージのリスト
    :param user: Userオブジェクト（オプション）
    :param session: DBセッション（オプション）
    :param bot_id: Bot識別子（オプション）
    :return: 成功したかどうかを示すブール値
    """
    global used_reply_tokens
    
    # reply_tokenの再利用チェック（replyの場合のみ）
    if message_type == "reply" and bot_id:
        # bot_idごとのトークンセットを初期化（存在しなければ）
        if bot_id not in used_reply_tokens:
            used_reply_tokens[bot_id] = set()
            
        token_preview = identifier[:10] + "..." if identifier else "None"
        
        # このbotですでに使用したトークンかチェック
        if identifier in used_reply_tokens[bot_id]:
            print(f"WARNING: Attempt to reuse reply_token for bot {bot_id}: {token_preview}")
            if user and session:
                log_message(session, user, "error", f"Reply token reuse detected for bot {bot_id}: {token_preview}")
            return False
        
        # 有効なトークンを記録
        used_reply_tokens[bot_id].add(identifier)
        print(f"New reply_token registered for bot {bot_id}: {token_preview}")
        
        # セットが大きくなりすぎないようにする（古いトークンは自動的に期限切れになる）
        if len(used_reply_tokens[bot_id]) > 500:
            used_reply_tokens[bot_id] = set(list(used_reply_tokens[bot_id])[-250:])
    
    max_retries = 3
    retry_count = 0
    backoff_factor = 2  # 指数バックオフの基数
    
    while retry_count < max_retries:
        try:
            # リクエストの詳細をログに記録
            msg_preview = str([m.type if hasattr(m, 'type') else 'unknown' for m in messages])
            botid_info = f" for bot {bot_id}" if bot_id else ""
            print(f"Attempting to send {message_type} message{botid_info}: {msg_preview}")
            
            if message_type == "reply":
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=identifier,
                        messages=messages
                    )
                )
                if user and session:
                    message_content = f"Reply送信成功{botid_info}: {[m.text if hasattr(m, 'text') else m.type for m in messages]}"
                    log_message(session, user, "sent", message_content)
                print(f"Successfully sent reply message{botid_info} with token: {token_preview}")
            else:  # push
                api.push_message(
                    PushMessageRequest(
                        to=identifier,
                        messages=messages
                    )
                )
                if user and session:
                    log_message(session, user, "sent", f"Push送信成功{botid_info}")
                print(f"Successfully sent push message{botid_info} to user: {identifier[:8]}...")
            
            return True
            
        except (RequestException, ConnectionError, Timeout, ProtocolError, HTTPError, socket.error) as e:
            retry_count += 1
            wait_time = backoff_factor ** retry_count
            
            botid_info = f" for bot {bot_id}" if bot_id else ""
            error_message = f"Network error in {message_type} attempt {retry_count}{botid_info}: {e} - Retrying in {wait_time}s"
            print(error_message)
            
            if user and session:
                log_message(session, user, "error", error_message)
            
            if retry_count == max_retries:
                print(f"Failed to send {message_type}{botid_info} after {max_retries} attempts")
                return False
            else:
                time.sleep(wait_time)
        
        except Exception as e:
            retry_count += 1
            wait_time = backoff_factor ** retry_count
            
            # 詳細なエラー情報をログに記録
            error_detail = str(e)
            response_info = ""
            
            # ApiExceptionからより詳細な情報を取得
            if hasattr(e, 'body') and hasattr(e, 'headers'):
                try:
                    error_body = e.body if isinstance(e.body, str) else str(e.body)
                    headers_info = str(e.headers) if hasattr(e, 'headers') else "No headers"
                    status_code = str(e.status) if hasattr(e, 'status') else "Unknown status"
                    response_info = f"\nStatus: {status_code}\nHeaders: {headers_info}\nBody: {error_body}"
                except:
                    response_info = "\nCould not extract response details"
            
            botid_info = f" for bot {bot_id}" if bot_id else ""
            error_message = f"Unexpected error in {message_type} attempt {retry_count}{botid_info}: {error_detail}{response_info} - Retrying in {wait_time}s"
            print(error_message)
            
            if user and session:
                log_message(session, user, "error", f"API error{botid_info}: {error_detail}")
            
            if retry_count == max_retries:
                print(f"Failed to send {message_type}{botid_info} after {max_retries} attempts due to: {error_detail}")
                return False
            else:
                time.sleep(wait_time)
    
    return False

# ログ記録関数
def log_message(session, user, message_type, content):
    """メッセージログを記録する関数"""
    try:
        log = MessageLog(
            user_id=user.id,
            message_type=message_type,
            message_content=content
        )
        session.add(log)
        session.commit()
    except SQLAlchemyError as e:
        print(f"Failed to log message: {e}")
        session.rollback()
    except Exception as e:
        print(f"Unexpected error while logging message: {e}")
        session.rollback()

# エラーログ関数
def log_error(context, error, user=None, session=None):
    """エラーメッセージをログに記録し、セッションをロールバックする"""
    error_message = f"Error in {context}: {error}"
    print(error_message)
    if user and session:
        log_message(session, user, "error", error_message)
    if session:
        session.rollback()

# Flex Message生成関数
def create_exercise_video_flex_message(video_url, thumbnail_url):
    """
    運動メニュー動画のFlex Messageを生成する
    
    Args:
        video_url: YouTube動画のURL
        thumbnail_url: サムネイル画像のURL
    
    Returns:
        FlexMessage用の辞書
    """
    from linebot.v3.messaging import FlexMessage, FlexContainer
    
    flex_content = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": thumbnail_url,
            "size": "full",
            "aspectRatio": "16:9",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "uri": video_url
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "今週の運動メニュー",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1DB446"
                },
                {
                    "type": "text",
                    "text": "動画を見ながら一緒に運動しましょう",
                    "size": "sm",
                    "color": "#999999",
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "動画を見る",
                        "uri": video_url
                    }
                }
            ],
            "flex": 0
        }
    }
    
    return FlexMessage(
        alt_text="今週の運動メニュー",
        contents=FlexContainer.from_dict(flex_content)
    )
