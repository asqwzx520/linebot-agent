from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _client


def save_memory(category: str, content: str) -> str:
    """儲存一筆記憶到資料庫。"""
    try:
        _get_client().table("memories").insert({
            "category": category,
            "content": content,
        }).execute()
        return f"✅ 記憶已儲存：[{category}] {content}"
    except Exception as e:
        return f"❌ 儲存失敗：{e}"


def recall_memories(limit: int = 8) -> list[str]:
    """從資料庫讀取最近的記憶。"""
    try:
        result = (
            _get_client()
            .table("memories")
            .select("category, content")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [f"[{r['category']}] {r['content']}" for r in result.data]
    except Exception:
        return []


def delete_memory(keyword: str) -> str:
    """刪除包含關鍵字的記憶。"""
    try:
        result = (
            _get_client()
            .table("memories")
            .delete()
            .ilike("content", f"%{keyword}%")
            .execute()
        )
        count = len(result.data) if result.data else 0
        return f"✅ 已刪除 {count} 筆包含「{keyword}」的記憶。"
    except Exception as e:
        return f"❌ 刪除失敗：{e}"


def save_conversation(user_id: str, role: str, content: str) -> None:
    """儲存對話紀錄（非同步、失敗不影響主流程）。"""
    try:
        _get_client().table("conversations").insert({
            "user_id": user_id,
            "role": role,
            "content": content[:2000],  # 限制長度
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
