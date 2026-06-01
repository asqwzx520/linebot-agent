# LINE Bot AI 個人助理

## What This Is

個人使用的 LINE Bot AI 助理，整合 Google Gemini Agent，具備多工具呼叫能力。使用者傳訊息、圖片或文件，Bot 自動判斷需求並呼叫對應工具回應。

**Core Value:** 一個記得你、能幫你查資料、能看圖、還能生圖的 LINE 私人助理，全程免費。

---

## Context

- **使用者：** 個人使用（單人）
- **程度：** 初學者，需詳細步驟說明
- **平台：** Windows 11
- **目標：** 不用付費也能有強大的 AI 助理在 LINE 上隨時待命

---

## Architecture

```
使用者 LINE 訊息（文字/圖片/文件）
        ↓
  FastAPI Webhook（Python）
        ↓
  讀取長期記憶 ← Supabase
        ↓
  Gemini 1.5 Flash Agent
        ↓ Function Calling
┌─────────────────────────────────────┐
│ Tool 1: search_web    網路搜尋       │
│ Tool 2: save_memory   存記憶         │
│ Tool 3: load_memory   讀記憶         │
│ Tool 4: analyze_image 圖片/PDF分析   │
│ Tool 5: generate_image 生圖降級鏈    │
└─────────────────────────────────────┘
        ↓
  回覆 LINE + 更新記憶
```

---

## Tech Stack（全免費）

| 元件 | 技術 | 免費限制 |
|------|------|---------|
| AI 模型 | Google Gemini 1.5 Flash | 每分鐘 15 req |
| 後端框架 | Python 3.11 + FastAPI | 免費開源 |
| 訊息平台 | LINE Messaging API | 200則推播/月 |
| 長期記憶 DB | Supabase（PostgreSQL） | 500MB 免費 |
| 本地測試 | ngrok | 免費（有流量限制） |
| 正式部署 | Render.com | 免費（閒置15分鐘會睡眠） |

---

## Requirements

### Validated

（尚無 — 待實作驗證）

### Active

- [ ] **CORE-01：** 使用者傳文字訊息，Bot 用 Gemini 回覆
- [ ] **CORE-02：** Bot 能記住使用者說過的事（跨 session 長期記憶）
- [ ] **CORE-03：** Bot 能搜尋網路幫使用者查資料
- [ ] **CORE-04：** 使用者傳圖片或 PDF，Bot 能解析並回覆分析
- [ ] **IMG-01：** 使用者要求生圖，Bot 自動嘗試免費 Provider A
- [ ] **IMG-02：** Provider A 額度耗盡，自動切換 Provider B
- [ ] **IMG-03：** Provider B 額度耗盡，自動切換 Provider C
- [ ] **IMG-04：** 全部額度耗盡，回覆友善提示訊息
- [ ] **MEM-01：** 記憶包含個人偏好（喜好、習慣）
- [ ] **MEM-02：** 記憶包含專案/工作進度
- [ ] **MEM-03：** 記憶包含歷史對話重點

### Out of Scope（v1）

- 生影片功能 — 複雜度高，列為 v2
- 多用戶支援 — 個人使用，不需要
- 付費 API — 本專案全程使用免費方案

---

## Key Decisions

| 決策 | 理由 | 結果 |
|------|------|------|
| Gemini 而非 Claude/GPT | 有免費層、支援圖片、支援 Function Calling | 確定 |
| Supabase 做記憶庫 | 免費 PostgreSQL，不需自架資料庫 | 確定 |
| ngrok 先測試，再部署 Render | 初學者友善，先本地跑通再上線 | 確定 |
| 生圖用降級鏈（A→B→C） | 使用者要求：額度耗盡自動切換，不中斷服務 | 確定 |
| 生影片列 v2 | v1 先穩定生圖，影片複雜度高先延後 | 確定 |
| 新資料夾建立專案 | 避免與 knowledge-base 現有程式混合 | 確定 |

---

## Image Generation Fallback Chain（待研究）

```
[使用者要求生圖]
      ↓
嘗試 Provider A：Gemini Imagen（Google）
      ↓ 失敗/額度耗盡
嘗試 Provider B：Stability AI / Replicate 免費層
      ↓ 失敗/額度耗盡
嘗試 Provider C：Hugging Face 免費推理 API
      ↓ 全部失敗
回覆：「今日免費生圖額度已用完，明天再試」
```

實際 Provider 清單待研究階段確認。

---

## Long-term Memory Schema（初步規劃）

```sql
-- Supabase 資料表設計（草稿）
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT DEFAULT 'owner',           -- 個人使用固定值
  category TEXT,                          -- 'preference' | 'project' | 'conversation'
  content TEXT NOT NULL,                  -- 記憶內容
  embedding VECTOR(768),                  -- 語意搜尋用（可選）
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Evolution

此文件在每個 Phase 完成後更新。

**更新規則：**
1. 需求完成 → 移至 Validated
2. 需求取消 → 移至 Out of Scope 並說明原因
3. 新需求出現 → 加入 Active
4. 決策更新 → 更新 Key Decisions 表格

---

*Last updated: 2026-06-02 — 初始化*
