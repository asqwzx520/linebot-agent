from duckduckgo_search import DDGS


def search_web(query: str) -> str:
    """搜尋網路，回傳格式化的搜尋結果。"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return f"搜尋「{query}」沒有找到結果。"

        lines = [f"🔍 搜尋「{query}」的結果：\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", "")[:200]
            href = r.get("href", "")
            lines.append(f"{i}. **{title}**\n   {body}\n   🔗 {href}\n")

        return "\n".join(lines)
    except Exception as e:
        return f"搜尋時發生錯誤：{e}"
