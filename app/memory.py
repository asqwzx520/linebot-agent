"""
長期記憶 + 對話歷史
記憶依 user_id 完全隔離，每個用戶只看到自己的記憶。
"""

from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

_client = None

def _get_client():
    global _client
    if _client is None:
        # 優先使用 service_role key（完整存取，繞過 RLS）
        # 若未設定則降回 anon key（舊相容）
        key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
        _client = create_client(SUPABASE_URL, key)
    return _client


# ── 長期記憶（依 user_id 隔離）────────────────────────────────────────────

def save_memory(user_id: str, category: str, content: str) -> str:
    """儲存一筆記憶到資料庫（屬於該用戶）。"""
    try:
        _get_client().table("memories").insert({
            "user_id":  user_id,
            "category": category,
            "content":  content,
        }).execute()
        return f"✅ 記憶已儲存：[{category}] {content}"
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


# ── 對話歷史（本來就依 user_id 隔離）──────────────────────────────────────

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
