"""
Gemini Agent — 核心 AI 處理邏輯。

模型降級鏈（免費方案，2026/6）：
  1. gemini-3.5-flash  — 最新主力，最強
  2. gemini-3.1-flash  — 第二選擇
  3. gemini-3.1-flash-lite — 高 RPM 備用（30 RPM）

多 API Key 支援：
  同一個 Key 的多個模型共享一個 Google Project 的額度。
  不同 Key（不同 Google 帳號）有各自獨立額度。
  降級順序：
    Key1 + 3.5-flash → Key2 + 3.5-flash → Key3 + 3.5-flash
    → Key1 + 3.1-flash → Key2 + 3.1-flash → ...
    → Key1 + 3.1-flash-lite → Key2 + 3.1-flash-lite → ...
"""

import io
import time
import PIL.Image
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from app.config import GEMINI_API_KEYS
from app.memory import (
    save_memory, recall_memories, delete_memory,
    save_conversation, get_recent_conversations,
)
from app.search import search_web as _search_web
from app.image_gen import generate_image as _generate_image

# ── 模型優先順序（品質高 → 低，但額度高 → 高）────────────────────────────
MODEL_CHAIN = [
    "gemini-3.5-flash",
    "gemini-3.1-flash",
    "gemini-3.1-flash-lite",
]

SYSTEM_PROMPT = """你是一個智慧、友善的個人 AI 助理，透過 LINE 與使用者互動。

【你的能力】
1. 一般問答與聊天
2. 搜尋網路取得最新資訊（天氣、新聞、股票等）
3. 儲存與回憶長期記憶（每位用戶的記憶完全分開）
4. 生成圖片

【工具使用時機】
- 問到時事/最新資料 → web_search
- 使用者說「記住」「幫我記」或提到重要個人資訊 → memory_save
- 需要回憶過去說過的事 → memory_recall
- 使用者說要刪除記憶 → memory_delete
- 使用者說「幫我畫」「生成圖片」「畫一個」→ image_generate

【生圖規則】
- prompt 必須用英文（品質更好）
- 成功時回覆：IMAGE_URL:<url>（系統會自動轉成圖片訊息）

【語言】
- 預設繁體中文
- 使用者用其他語言則跟著切換

【態度】
- 友善、簡潔、實用
- 不要過於冗長
"""


# ── Tool 定義（user_id 透過 closure 帶入）────────────────────────────────

def _make_tools(user_id: str):
    """為特定用戶建立工具函數（記憶操作都帶 user_id）。"""

    def web_search(query: str) -> str:
        """搜尋網路以取得最新資訊。適合查天氣、新聞、股票、即時資料。

        Args:
            query: 搜尋關鍵字或問題
        Returns:
            搜尋結果的摘要文字
        """
        return _search_web(query)

    def memory_save(category: str, content: str) -> str:
        """儲存重要資訊到長期記憶庫。使用者說「記住」「幫我記」時使用。

        Args:
            category: 分類，例如 preference（偏好）、project（專案）、note（備忘）、personal（個人）
            content: 要記住的具體內容
        Returns:
            確認訊息
        """
        # 防 Prompt Injection：限制長度、限制分類
        content  = content[:500].strip()
        category = category[:50].strip()
        allowed  = {"preference", "project", "note", "personal", "general"}
        if category not in allowed:
            category = "note"
        return save_memory(user_id, category, content)

    def memory_recall(keyword: str = "") -> str:
        """從長期記憶庫讀取記憶。需要回顧使用者說過的事時使用。

        Args:
            keyword: 想查詢的關鍵字（可留空以取得所有近期記憶）
        Returns:
            記憶列表文字
        """
        memories = recall_memories(user_id, limit=10)
        if not memories:
            return "目前沒有儲存任何記憶。"
        if keyword:
            filtered = [m for m in memories if keyword.lower() in m.lower()]
            memories = filtered if filtered else memories
        return "我記得的事：\n" + "\n".join(f"• {m}" for m in memories)

    def memory_delete(keyword: str) -> str:
        """刪除長期記憶庫中包含特定關鍵字的記憶。

        Args:
            keyword: 要刪除的記憶關鍵字
        Returns:
            確認訊息
        """
        return delete_memory(user_id, keyword)

    def image_generate(prompt: str) -> str:
        """生成圖片。使用者要求生圖時使用。prompt 請用英文以獲得最佳效果。

        Args:
            prompt: 圖片描述（英文），例如 'a cute orange cat sitting on a cloud'
        Returns:
            圖片 URL（IMAGE_URL:<url>）或錯誤訊息
        """
        result = _generate_image(prompt)
        if result.startswith("ERROR:"):
            return result
        return f"IMAGE_URL:{result}"

    return [web_search, memory_save, memory_recall, memory_delete, image_generate]


# ── 模型降級鏈核心 ────────────────────────────────────────────────────────

def _call_with_fallback(user_id: str, full_input: str, gemini_history: list) -> str:
    """
    嘗試所有 Key × Model 組合，第一個成功的就回傳。
    順序：Key1+3.5 → Key2+3.5 → Key3+3.5 → Key1+3.1 → Key2+3.1 → ...
    """
    tools = _make_tools(user_id)
    last_error = None

    for model_name in MODEL_CHAIN:
        for api_key in GEMINI_API_KEYS:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    tools=tools,
                    system_instruction=SYSTEM_PROMPT,
                )
                chat = model.start_chat(
                    history=gemini_history,
                    enable_automatic_function_calling=True,
                )
                response = chat.send_message(full_input)
                return response.text

            except (ResourceExhausted, ServiceUnavailable) as e:
                # 額度用完或服務不可用 → 換下一個
                last_error = e
                time.sleep(0.3)
                continue
            except Exception as e:
                # 其他錯誤（模型不存在等）→ 換下一個模型
                last_error = e
                break  # 跳過這個模型的其他 key，直接換模型

    raise RuntimeError(f"所有模型與 Key 都失敗：{last_error}")


def _history_to_gemini(history: list[dict]) -> list[dict]:
    """將 Supabase 對話記錄轉換成 Gemini 格式。"""
    result = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        result.append({"role": role, "parts": [turn["content"]]})
    return result


# ── 主處理函數 ────────────────────────────────────────────────────────────

def process_text(user_id: str, text: str) -> tuple[str, str | None]:
    """
    處理文字訊息。
    回傳 (reply_text, image_url_or_None)
    """
    # 載入近期對話歷史
    history = get_recent_conversations(user_id, limit=6)
    gemini_history = _history_to_gemini(history)

    # 加入該用戶的記憶作為背景 context
    # 使用 XML 標記結構化分隔，降低 Prompt Injection 風險
    memories = recall_memories(user_id, limit=5)
    if memories:
        mem_items = "\n".join(f"  <item>{m}</item>" for m in memories)
        mem_block = f"<user_memories>\n{mem_items}\n</user_memories>\n\n"
        full_input = mem_block + text
    else:
        full_input = text

    reply = _call_with_fallback(user_id, full_input, gemini_history)

    # 儲存對話
    save_conversation(user_id, "user", text)
    save_conversation(user_id, "assistant", reply)

    # 解析圖片 URL
    image_url = None
    if "IMAGE_URL:" in reply:
        lines = reply.splitlines()
        kept, found_url = [], None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("IMAGE_URL:"):
                found_url = stripped.split("IMAGE_URL:", 1)[1].strip()
            else:
                kept.append(line)
        image_url = found_url
        reply = "\n".join(kept).strip() or "圖片已生成！"

    return reply, image_url


def process_image(user_id: str, image_bytes: bytes, caption: str = "") -> str:
    """處理使用者傳送的圖片（含可選文字說明）。"""
    for api_key in GEMINI_API_KEYS:
        for model_name in ["gemini-3.5-flash", "gemini-3.1-flash", "gemini-3.1-flash-lite"]:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_PROMPT,
                )
                pil_image = PIL.Image.open(io.BytesIO(image_bytes))
                prompt = caption if caption else "請詳細描述這張圖片，並提供你認為有用的分析或見解。"
                response = model.generate_content([prompt, pil_image])
                reply = response.text
                save_conversation(user_id, "user", f"[圖片] {caption}")
                save_conversation(user_id, "assistant", reply)
                return reply
            except (ResourceExhausted, ServiceUnavailable):
                time.sleep(0.3)
                continue
            except Exception:
                break

    return "圖片分析暫時無法使用，請稍後再試。"


def process_pdf(user_id: str, pdf_bytes: bytes, filename: str = "文件") -> str:
    """處理 PDF 文件，擷取文字後送給 Gemini 摘要。"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages[:20]:
            pages_text.append(page.extract_text() or "")
        content = "\n".join(pages_text).strip()

        if not content:
            return "無法從這份 PDF 中提取文字（可能是掃描版圖片 PDF）。"

        prompt = f"以下是 PDF「{filename}」的內容，請提供重點摘要：\n\n{content[:8000]}"

        for api_key in GEMINI_API_KEYS:
            for model_name in ["gemini-3.5-flash", "gemini-3.1-flash", "gemini-3.1-flash-lite"]:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=SYSTEM_PROMPT,
                    )
                    response = model.generate_content(prompt)
                    reply = response.text
                    save_conversation(user_id, "user", f"[PDF：{filename}]")
                    save_conversation(user_id, "assistant", reply)
                    return reply
                except (ResourceExhausted, ServiceUnavailable):
                    time.sleep(0.3)
                    continue
                except Exception:
                    break

        return "PDF 分析暫時無法使用，所有模型額度已用完，請稍後再試。"

    except Exception as e:
        return f"PDF 解析失敗：{e}"
