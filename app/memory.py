"""
長期記憶 + 對話歷史 + 用戶設定
記憶依 user_id 完全隔離，每個用戶只看到自己的記憶。
"""

from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

_client = None

# 每位用戶最多可儲存的記憶筆數
MAX_MEMORIES_PER_USER = 100


def _get_client():
    global _client
    if _client is None:
        key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
        _client = create_client(SUPABASE_URL, key)
    return _client


# ── 長期記憶（依 user_id 隔離）────────────────────────────────────────────

def count_memories(user_id: str) -> int:
    """統計該用戶目前的記憶筆數。"""
    try:
        result = (
            _get_client()
            .table("memories")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        return result.count or 0
    except Exception:
        return 0


def save_memory(user_id: str, category: str, content: str) -> str:
    """儲存一筆記憶到資料庫（屬於該用戶）。超過上限時拒絕並提示。"""
    try:
        current = count_memories(user_id)
        if current >= MAX_MEMORIES_PER_USER:
            return (
                f"⚠️ 記憶庫已滿（{current}/{MAX_MEMORIES_PER_USER} 筆）。\n"
                f"請先說「刪除記憶 <關鍵字>」刪除不需要的記憶後再儲存。"
            )
        _get_client().table("memories").insert({
            "user_id":  user_id,
            "category": category,
            "content":  content,
        }).execute()
        return f"✅ 記憶已儲存（{current + 1}/{MAX_MEMORIES_PER_USER}）：[{category}] {content}"
    except Exception as e:
        return f"❌ 儲存失敗：{e}"


def recall_memories(user_id: str, limit: int = 8) -> list[str]:
    """從資料庫讀取該用戶的最近記憶。"""
    try:
        result = (
            _get_client()
            .table("memories")
            .select("category, content")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [f"[{r['category']}] {r['content']}" for r in result.data]
    except Exception:
        return []


def delete_memory(user_id: str, keyword: str) -> str:
    """刪除該用戶包含關鍵字的記憶。"""
    try:
        result = (
            _get_client()
            .table("memories")
            .delete()
            .eq("user_id", user_id)
            .ilike("content", f"%{keyword}%")
            .execute()
        )
        count = len(result.data) if result.data else 0
        return f"✅ 已刪除 {count} 筆包含「{keyword}」的記憶。"
    except Exception as e:
        return f"❌ 刪除失敗：{e}"


def get_memory_status(user_id: str) -> str:
    """回傳記憶使用狀況的文字摘要。"""
    current = count_memories(user_id)
    bar_filled = int(current / MAX_MEMORIES_PER_USER * 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    return (
        f"🧠 記憶庫使用狀況\n"
        f"[{bar}] {current}/{MAX_MEMORIES_PER_USER} 筆\n"
        f"剩餘空間：{MAX_MEMORIES_PER_USER - current} 筆"
    )


# ── 對話歷史──────────────────────────────────────────────────────────────

def save_conversation(user_id: str, role: str, content: str) -> None:
    """儲存對話紀錄（失敗不影響主流程）。"""
    try:
        _get_client().table("conversations").insert({
            "user_id": user_id,
            "role":    role,
            "content": content[:2000],
        }).execute()
    except Exception:
        pass


def get_recent_conversations(user_id: str, limit: int = 6) -> list[dict]:
    """取得該使用者的最近對話（由舊到新）。"""
    try:
        result = (
            _get_client()
            .table("conversations")
            .select("role, content")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(result.data))
    except Exception:
        return []


def export_conversations(user_id: str, limit: int = 100) -> str:
    """匯出用戶的對話記錄（最多 limit 筆，由舊到新）。"""
    try:
        result = (
            _get_client()
            .table("conversations")
            .select("role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = list(reversed(result.data))
        if not rows:
            return "目前沒有對話記錄。"

        lines = [f"📤 對話記錄（最近 {len(rows)} 則）\n{'─' * 20}"]
        for r in rows:
            role_label = "👤 你" if r["role"] == "user" else "🤖 Bot"
            # 截短超長內容
            content = r["content"]
            if len(content) > 200:
                content = content[:200] + "…"
            lines.append(f"{role_label}：{content}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 匯出失敗：{e}"


def clear_conversations(user_id: str) -> str:
    """清除該用戶的所有對話記錄。"""
    try:
        result = (
            _get_client()
            .table("conversations")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
        count = len(result.data) if result.data else 0
        return f"✅ 已清除 {count} 筆對話記錄。"
    except Exception as e:
        return f"❌ 清除失敗：{e}"


# ── 用戶設定（儲存於 user_settings 資料表）──────────────────────────────

_VALID_LANGUAGES = {
    "中文": "zh-tw", "繁中": "zh-tw", "zh-tw": "zh-tw",
    "簡中": "zh-cn", "zh-cn": "zh-cn",
    "英文": "en", "english": "en", "en": "en",
}

_DEFAULT_SETTINGS = {"language": "zh-tw"}


def get_user_settings(user_id: str) -> dict:
    """取得用戶設定，若不存在則回傳預設值。"""
    try:
        result = (
            _get_client()
            .table("user_settings")
            .select("language")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return dict(_DEFAULT_SETTINGS)
    except Exception:
        return dict(_DEFAULT_SETTINGS)


def set_user_language(user_id: str, lang_input: str) -> str:
    """設定用戶的語言偏好。"""
    lang_key = lang_input.strip().lower()
    lang_code = _VALID_LANGUAGES.get(lang_key)
    if not lang_code:
        valid = "、".join(_VALID_LANGUAGES.keys())
        return f"❌ 不支援的語言。\n可選：{valid}"
    try:
        _get_client().table("user_settings").upsert({
            "user_id":  user_id,
            "language": lang_code,
        }).execute()
        label = {"zh-tw": "繁體中文", "zh-cn": "簡體中文", "en": "English"}[lang_code]
        return f"✅ 語言已設定為：{label}"
    except Exception as e:
        return f"❌ 設定失敗：{e}"


def format_settings_display(user_id: str) -> str:
    """回傳設定摘要文字。"""
    s = get_user_settings(user_id)
    lang_label = {"zh-tw": "繁體中文 🇹🇼", "zh-cn": "簡體中文 🇨🇳", "en": "English 🇬🇧"}.get(
        s.get("language", "zh-tw"), "繁體中文 🇹🇼"
    )
    mem_count = count_memories(user_id)
    return (
        f"⚙️ 你的設定\n"
        f"{'─' * 20}\n"
        f"🌐 語言：{lang_label}\n"
        f"🧠 記憶：{mem_count}/{MAX_MEMORIES_PER_USER} 筆\n\n"
        f"可用指令：\n"
        f"• /設定 語言 中文\n"
        f"• /設定 語言 英文\n"
        f"• /記憶 — 查看記憶使用量\n"
        f"• /匯出 — 匯出對話記錄\n"
        f"• /清除對話 — 清空對話歷史"
    )
