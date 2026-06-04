"""
LINE Webhook 事件處理器。
接收 LINE 事件 → 呼叫 Gemini Agent → 回覆使用者。
"""

import asyncio
import logging

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    FileMessageContent,
    FollowEvent,
)
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage,
)
from app.config import LINE_CHANNEL_ACCESS_TOKEN
from app.gemini_agent import process_text, process_image, process_pdf, process_excel
from app.rate_limiter import is_rate_limited

logger = logging.getLogger(__name__)

_line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

MAX_PDF_SIZE   = 10 * 1024 * 1024  # 10 MB
MAX_EXCEL_SIZE =  5 * 1024 * 1024  #  5 MB


def _send_reply(reply_token: str, messages: list) -> None:
    with ApiClient(_line_config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=messages)
        )


def _download_content(message_id: str) -> bytes:
    with ApiClient(_line_config) as api_client:
        blob = MessagingApiBlob(api_client)
        data = blob.get_message_content(message_id=message_id)
        if isinstance(data, bytes):
            return data
        return b"".join(data)


async def handle_line_events(events: list) -> None:
    """處理所有傳入的 LINE 事件。"""
    for event in events:
        try:
            await _dispatch(event)
        except Exception as e:
            # 只記錄日誌，回覆通用訊息（不洩漏技術細節）
            logger.error("Event dispatch error: %s", e, exc_info=True)
            if hasattr(event, "reply_token"):
                try:
                    _send_reply(
                        event.reply_token,
                        [TextMessage(text="處理時發生錯誤，請稍後再試。")],
                    )
                except Exception:
                    pass


async def _dispatch(event) -> None:
    loop = asyncio.get_event_loop()

    # ── 新好友 ──────────────────────────────────────────────────────────────
    if isinstance(event, FollowEvent):
        _send_reply(
            event.reply_token,
            [TextMessage(
                text=(
                    "👋 你好！我是你的個人 AI 助理！\n\n"
                    "我可以：\n"
                    "💬 回答問題和聊天\n"
                    "🔍 搜尋網路取得最新資訊\n"
                    "🧠 記住你說的重要事情\n"
                    "🖼 分析圖片和 PDF\n"
                    "📊 分析 Excel / CSV 數據\n"
                    "🎨 幫你生成圖片\n\n"
                    "直接傳訊息就可以開始了！"
                )
            )],
        )
        return

    if not isinstance(event, MessageEvent):
        return

    reply_token = event.reply_token
    user_id     = event.source.user_id
    msg         = event.message

    # ── 速率限制 ─────────────────────────────────────────────────────────────
    if is_rate_limited(user_id):
        _send_reply(reply_token, [TextMessage(
            text="⚠️ 請求太頻繁，請稍後再試（每分鐘最多 10 則）。"
        )])
        return

    # ── 文字訊息 ─────────────────────────────────────────────────────────────
    if isinstance(msg, TextMessageContent):
        reply_text, image_url = await loop.run_in_executor(
            None, process_text, user_id, msg.text
        )
        messages = []
        if reply_text:
            for chunk in _chunk_text(reply_text, 4500):
                messages.append(TextMessage(text=chunk))
        if image_url:
            messages.append(ImageMessage(
                original_content_url=image_url,
                preview_image_url=image_url,
            ))
        _send_reply(reply_token, messages or [TextMessage(text="（空回覆）")])

    # ── 圖片訊息 ─────────────────────────────────────────────────────────────
    elif isinstance(msg, ImageMessageContent):
        image_bytes = await loop.run_in_executor(None, _download_content, msg.id)
        reply_text  = await loop.run_in_executor(
            None, process_image, user_id, image_bytes, ""
        )
        _send_reply(reply_token, [TextMessage(text=reply_text[:4500])])

    # ── 檔案訊息（PDF / Excel / CSV）────────────────────────────────────────
    elif isinstance(msg, FileMessageContent):
        filename   = msg.file_name
        fname_low  = filename.lower()

        if fname_low.endswith(".pdf"):
            file_bytes = await loop.run_in_executor(None, _download_content, msg.id)
            if len(file_bytes) > MAX_PDF_SIZE:
                _send_reply(reply_token, [TextMessage(
                    text="PDF 檔案過大，請上傳 10MB 以內的檔案。"
                )])
                return
            reply_text = await loop.run_in_executor(
                None, process_pdf, user_id, file_bytes, filename
            )

        elif fname_low.endswith((".xlsx", ".xls", ".csv")):
            file_bytes = await loop.run_in_executor(None, _download_content, msg.id)
            if len(file_bytes) > MAX_EXCEL_SIZE:
                _send_reply(reply_token, [TextMessage(
                    text="檔案過大，請上傳 5MB 以內的 Excel / CSV 檔案。"
                )])
                return
            # 先告知用戶分析中（檔案大時可能需要幾秒）
            reply_text = await loop.run_in_executor(
                None, process_excel, user_id, file_bytes, filename
            )

        else:
            ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "?"
            reply_text = (
                f"目前支援的格式：PDF、Excel（.xlsx/.xls）、CSV。\n"
                f"不支援 .{ext} 格式。"
            )

        # 長回覆分段傳送
        chunks = _chunk_text(reply_text, 4500)
        _send_reply(reply_token, [TextMessage(text=chunks[0])])

    else:
        _send_reply(reply_token, [TextMessage(
            text="目前支援：文字、圖片、PDF、Excel（.xlsx/.xls）、CSV。"
        )])


def _chunk_text(text: str, size: int) -> list[str]:
    """將長文字切割成 LINE 可接受的大小。"""
    return [text[i:i + size] for i in range(0, len(text), size)]
