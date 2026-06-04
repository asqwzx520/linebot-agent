"""
FastAPI 主程式 — LINE Bot Webhook 入口。
"""

import os
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from app.config import LINE_CHANNEL_SECRET
from app.line_handler import handle_line_events

# ── Sentry 錯誤追蹤（選用）────────────────────────────────────────────────
_SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,   # 10% 效能追蹤
            send_default_pii=False,   # 不傳送個資
        )
    except ImportError:
        pass  # sentry-sdk 未安裝時安靜跳過

app = FastAPI(title="LINE Bot AI Agent")
parser = WebhookParser(LINE_CHANNEL_SECRET)


@app.get("/")
async def root():
    return {"status": "LINE Bot AI Agent is running 🤖"}


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    try:
        events = parser.parse(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    await handle_line_events(events)
    return {"status": "ok"}
