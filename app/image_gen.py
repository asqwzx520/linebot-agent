"""
生圖降級鏈：
  A: Pollinations.ai FLUX（免費、無需 API Key）
  B: Hugging Face SDXL（免費、需 HF_TOKEN）
  C: Pollinations.ai Turbo（備用，較快但品質稍低）
"""

import urllib.parse
import httpx
import time

from app.config import HF_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

TIMEOUT = 60  # seconds


# ── Provider A ──────────────────────────────────────────────────────────────

def _try_pollinations_flux(prompt: str) -> str | None:
    """Pollinations.ai FLUX 模型（免費、高品質）。"""
    try:
        encoded = urllib.parse.quote(prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1024&height=1024&nologo=true&model=flux&enhance=true"
        )
        r = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            # 上傳到 Supabase Storage 取得穩定 URL
            stable_url = _upload_to_supabase(r.content)
            return stable_url or url
        return None
    except Exception:
        return None


# ── Provider B ──────────────────────────────────────────────────────────────

def _try_huggingface_sdxl(prompt: str) -> str | None:
    """Hugging Face Inference API — Stable Diffusion XL（需 HF_TOKEN）。"""
    if not HF_TOKEN:
        return None
    try:
        r = httpx.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt},
            timeout=TIMEOUT,
        )
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            return _upload_to_supabase(r.content)
        return None
    except Exception:
        return None


# ── Provider C ──────────────────────────────────────────────────────────────

def _try_pollinations_turbo(prompt: str) -> str | None:
    """Pollinations.ai Turbo（備用、較快）。"""
    try:
        encoded = urllib.parse.quote(prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=512&height=512&nologo=true&model=turbo"
        )
        r = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            stable_url = _upload_to_supabase(r.content)
            return stable_url or url
        return None
    except Exception:
        return None


# ── Supabase Storage ─────────────────────────────────────────────────────────

def _upload_to_supabase(image_bytes: bytes) -> str | None:
    """上傳圖片到 Supabase Storage，回傳公開 URL。"""
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not SUPABASE_URL or not key:
        return None
    try:
        from supabase import create_client
        import uuid
        client = create_client(SUPABASE_URL, key)
        filename = f"gen_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.jpg"
        client.storage.from_("images").upload(
            filename, image_bytes, {"content-type": "image/jpeg"}
        )
        return client.storage.from_("images").get_public_url(filename)
    except Exception:
        return None


# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate_image(prompt: str) -> str:
    """
    生圖降級鏈：A → B → C。
    成功回傳圖片 URL（字串以 https:// 開頭）。
    全部失敗回傳 ERROR: 開頭的訊息。
    """
    providers = [
        ("Pollinations FLUX", _try_pollinations_flux),
        ("HuggingFace SDXL", _try_huggingface_sdxl),
        ("Pollinations Turbo", _try_pollinations_turbo),
    ]

    for name, fn in providers:
        try:
            result = fn(prompt)
            if result and result.startswith("http"):
                return result
        except Exception:
            continue

    return "ERROR: 今日免費生圖額度已用完，請明天再試，或設定 HF_TOKEN 增加額度。"
