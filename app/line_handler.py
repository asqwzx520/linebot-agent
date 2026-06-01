"""
LINE Webhook 事件處理器。
接收 LINE 事件 → 呼叫 Gemini Agent → 回覆使用者。
"""

import asyncio
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
from app.gemini_agent import process_text, process_image, process_pdf

_line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)


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
            # 嘗試回覆錯誤訊息
            if hasattr(event, "reply_token"):
                try:
                    _send_reply(
                        event.reply_token,
                        [TextMessage(text=f"處理時發生錯誤，請再試一次。\n({type(e).__name__}: {e})")],
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
                    "🎨 幫你生成圖片\n\n"
                    "直接傳訊息就可以開始了！"
                )
            )],
        )
        return

    if not isinstance(event, MessageEvent):
        return

    reply_token = event.reply_token
    user_id = event.source.user_id
    msg = event.message

    # ── 文字訊息 ─────────────────────────────────────────────────────────────
    if isinstance(msg, TextMessageContent):
        reply_text, image_url = await loop.run_in_executor(
            None, process_text, user_id, msg.text
        )
        messages = []
        if reply_text:
            # LINE 單則訊息最多 5000 字
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
        reply_text = await loop.run_in_executor(
            None, process_image, user_id, image_bytes, ""
        )
        _send_reply(reply_token, [TextMessage(text=reply_text[:4500])])

    # ── 檔案訊息（PDF）──────────────────────────────────────────────────────
    elif isinstance(msg, FileMessageContent):
        filename = msg.file_name
        if filename.lower().endswith(".pdf"):
            file_bytes = await loop.run_in_executor(None, _download_content, msg.id)
            reply_text = await loop.run_in_executor(
                None, process_pdf, user_id, file_bytes, filename
            )
        else:
            ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "?"
            reply_text = f"目前只支援 PDF 文件，不支援 {ext} 格式。"
        _send_reply(reply_token, [TextMessage(text=reply_text[:4500])])

    else:
        _send_reply(reply_token, [TextMessage(text="目前支援文字、圖片和 PDF。")])


def _chunk_text(text: str, size: int) -> list[str]:
    """將長文字切割成 LINE 可接受的大小。"""
    return [text[i:i + size] for i in range(0, len(text), size)]
