"""
FastAPI 主程式 — LINE Bot Webhook 入口。
"""

from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from app.config import LINE_CHANNEL_SECRET
from app.line_handler import handle_line_events

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
