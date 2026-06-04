"""
LINE Push Message API 封裝。
用於在背景任務完成後主動推播訊息給用戶（不需 reply_token）。
"""

import logging
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
    VideoMessage,
)
from app.config import LINE_CHANNEL_ACCESS_TOKEN

logger = logging.getLogger(__name__)
_line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)


def push_text(user_id: str, text: str) -> None:
    """主動傳送文字訊息給用戶。"""
    try:
        with ApiClient(_line_config) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=text[:4500])],
                )
            )
    except Exception as e:
        logger.error("push_text failed user=%s: %s", user_id, e)


def push_video(user_id: str, video_url: str, preview_url: str, caption: str = "") -> None:
    """主動傳送影片訊息給用戶。"""
    messages = []
    if caption:
        messages.append(TextMessage(text=caption[:4500]))
    messages.append(
        VideoMessage(
            original_content_url=video_url,
            preview_image_url=preview_url,
        )
    )
    try:
        with ApiClient(_line_config) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(to=user_id, messages=messages)
            )
    except Exception as e:
        logger.error("push_video failed user=%s: %s", user_id, e)
        # fallback: 傳文字告知影片 URL
        push_text(user_id, f"🎬 影片已生成（請點選連結觀看）：\n{video_url}")
