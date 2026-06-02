import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET       = os.getenv("LINE_CHANNEL_SECRET", "")
SUPABASE_URL              = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY         = os.getenv("SUPABASE_ANON_KEY", "")       # 前端公開用（不給後端用）
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") # 後端專用，完整存取權限
HF_TOKEN                  = os.getenv("HF_TOKEN", "")
PORT                      = int(os.getenv("PORT", "8000"))

# ── 多個 Gemini API Key（不同 Google 帳號 = 各自獨立額度）──────────────────
# 必填：GEMINI_API_KEY
# 選填：GEMINI_API_KEY_2、GEMINI_API_KEY_3（不同 Google 帳號取得）
def _collect_gemini_keys() -> list[str]:
    keys = []
    for env in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
        k = os.getenv(env, "").strip()
        if k:
            keys.append(k)
    return keys

GEMINI_API_KEYS: list[str] = _collect_gemini_keys()
GEMINI_API_KEY: str = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
