"""
AI 影片生成降級鏈：
  A: Kling AI（高品質，需 KLING_API_KEY + KLING_API_SECRET）
  B: HuggingFace text-to-video（免費，需 HF_TOKEN，品質較低）
  C: 友善錯誤訊息

影片以非同步方式生成，完成後透過 push_message 推播給用戶。
"""

import asyncio
import logging
import time
import uuid

import httpx

from app.config import (
    KLING_API_KEY, KLING_API_SECRET,
    HF_TOKEN,
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY,
)
from app.push_message import push_text, push_video

logger = logging.getLogger(__name__)

# 影片生成最長等待時間（秒）
VIDEO_TIMEOUT = 300   # 5 分鐘
POLL_INTERVAL = 8     # 每 8 秒輪詢一次

# Kling AI 免費模型
KLING_MODEL  = "kling-v1"
KLING_ASPECT = "16:9"
KLING_DURATION = "5"    # 5 秒影片（免費方案最長）


# ── 主入口（背景呼叫）─────────────────────────────────────────────────────

async def generate_and_push(user_id: str, prompt: str) -> None:
    """
    背景生成影片，完成後透過 LINE Push Message 傳給用戶。
    此函數由 asyncio.create_task() 呼叫，不阻塞 Webhook 回覆。
    """
    logger.info("video_gen start user=%s prompt=%.60s", user_id, prompt)

    # ① 先生成縮圖（用 Pollinations，幾乎即時）
    preview_url = await _generate_preview(prompt)

    # ② 嘗試生成影片
    video_url = None

    if KLING_API_KEY and KLING_API_SECRET:
        video_url = await _kling_generate(prompt)
        if video_url:
            logger.info("video_gen: Kling success user=%s", user_id)

    if not video_url and HF_TOKEN:
        video_url = await _huggingface_generate(prompt)
        if video_url:
            logger.info("video_gen: HuggingFace success user=%s", user_id)

    # ③ 推播結果
    if video_url:
        push_video(
            user_id,
            video_url=video_url,
            preview_url=preview_url or _default_preview(),
            caption="🎬 影片生成完成！",
        )
    else:
        push_text(
            user_id,
            "❌ 影片生成失敗。\n\n"
            "可能原因：\n"
            "• Kling AI 未設定 API Key\n"
            "• HuggingFace Token 未設定或額度不足\n\n"
            "請到 klingai.com 申請免費 API Key 後，"
            "在 Render 設定 KLING_API_KEY 和 KLING_API_SECRET。"
        )


# ── Kling AI ──────────────────────────────────────────────────────────────

def _kling_auth_header() -> dict:
    """生成 Kling AI JWT Bearer Token。"""
    try:
        import jwt as pyjwt
        payload = {
            "iss": KLING_API_KEY,
            "exp": int(time.time()) + 1800,
            "nbf": int(time.time()) - 5,
        }
        token = pyjwt.encode(payload, KLING_API_SECRET, algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}
    except Exception:
        # 若未安裝 PyJWT，嘗試直接用 API Key
        return {"Authorization": f"Bearer {KLING_API_KEY}"}


async def _kling_generate(prompt: str) -> str | None:
    """
    Kling AI 文字生成影片。
    步驟：建立任務 → 輪詢狀態 → 取得影片 URL
    """
    headers = {**_kling_auth_header(), "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 建立生成任務
            create_resp = await client.post(
                "https://api.klingai.com/v1/videos/text2video",
                headers=headers,
                json={
                    "model":      KLING_MODEL,
                    "prompt":     prompt,
                    "aspect_ratio": KLING_ASPECT,
                    "duration":   KLING_DURATION,
                    "cfg_scale":  0.5,
                },
            )
            data = create_resp.json()
            if create_resp.status_code != 200:
                logger.warning("Kling create failed: %s", data)
                return None

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                return None

        # 輪詢任務狀態
        deadline = time.time() + VIDEO_TIMEOUT
        async with httpx.AsyncClient(timeout=20) as client:
            while time.time() < deadline:
                await asyncio.sleep(POLL_INTERVAL)
                status_resp = await client.get(
                    f"https://api.klingai.com/v1/videos/text2video/{task_id}",
                    headers=headers,
                )
                status_data = status_resp.json().get("data", {})
                task_status = status_data.get("task_status", "")

                if task_status == "succeed":
                    videos = status_data.get("task_result", {}).get("videos", [])
                    if videos:
                        return videos[0].get("url")
                    return None
                elif task_status in ("failed", "cancelled"):
                    logger.warning("Kling task %s: %s", task_id, task_status)
                    return None
                # processing / waiting → continue polling

        logger.warning("Kling task %s timed out", task_id)
        return None

    except Exception as e:
        logger.error("Kling generate error: %s", e)
        return None


# ── HuggingFace ──────────────────────────────────────────────────────────

async def _huggingface_generate(prompt: str) -> str | None:
    """
    HuggingFace Inference API — text-to-video。
    回傳上傳到 Supabase 後的公開 URL。
    """
    HF_VIDEO_MODEL = "ali-vilab/text-to-video-ms-1.7b"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type":  "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=VIDEO_TIMEOUT) as client:
            resp = await client.post(
                f"https://api-inference.huggingface.co/models/{HF_VIDEO_MODEL}",
                headers=headers,
                json={"inputs": prompt},
            )
            if resp.status_code != 200:
                logger.warning("HF video failed: %d", resp.status_code)
                return None
            content_type = resp.headers.get("content-type", "")
            if "video" in content_type or "octet-stream" in content_type:
                video_bytes = resp.content
                return await asyncio.to_thread(_upload_video_to_supabase, video_bytes)
        return None
    except Exception as e:
        logger.error("HuggingFace video error: %s", e)
        return None


# ── Supabase Storage ─────────────────────────────────────────────────────

def _upload_video_to_supabase(video_bytes: bytes) -> str | None:
    """上傳影片到 Supabase Storage（videos bucket），回傳公開 URL。"""
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not SUPABASE_URL or not key:
        return None
    try:
        from supabase import create_client
        client   = create_client(SUPABASE_URL, key)
        filename = f"vid_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.mp4"
        client.storage.from_("videos").upload(
            filename, video_bytes, {"content-type": "video/mp4"}
        )
        return client.storage.from_("videos").get_public_url(filename)
    except Exception as e:
        logger.error("Supabase video upload error: %s", e)
        return None


# ── 縮圖 ─────────────────────────────────────────────────────────────────

async def _generate_preview(prompt: str) -> str | None:
    """使用 Pollinations 生成影片縮圖（同步上傳，async 包裝）。"""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1280&height=720&nologo=true&model=flux"
        )
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
                # 上傳到 Supabase 取得穩定 URL
                uploaded = await asyncio.to_thread(_upload_preview_to_supabase, r.content)
                return uploaded or url
    except Exception:
        pass
    return _default_preview()


def _upload_preview_to_supabase(image_bytes: bytes) -> str | None:
    """上傳縮圖到 Supabase images bucket。"""
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not SUPABASE_URL or not key:
        return None
    try:
        from supabase import create_client
        client   = create_client(SUPABASE_URL, key)
        filename = f"thumb_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.jpg"
        client.storage.from_("images").upload(
            filename, image_bytes, {"content-type": "image/jpeg"}
        )
        return client.storage.from_("images").get_public_url(filename)
    except Exception:
        return None


def _default_preview() -> str:
    """預設縮圖（純色背景）。"""
    return "https://image.pollinations.ai/prompt/video%20thumbnail?width=1280&height=720&nologo=true"
