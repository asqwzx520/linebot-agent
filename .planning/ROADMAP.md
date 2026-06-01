# Roadmap — LINE Bot AI 個人助理

**總覽：6 個 Phase，從零到上線**

| # | Phase | 目標 | 需求 | 預估時間 |
|---|-------|------|------|---------|
| 1 | 環境準備 | 所有帳號與工具就位 | 無（準備階段） | 1-2 小時 |
| 2 | 基本對話 Bot | LINE 能收發 Gemini 訊息 | CORE-01~03 | 2-3 小時 |
| 3 | Agent + 記憶 + 搜尋 | 工具呼叫 + 長期記憶 | MEM-01~05, SEARCH-01~03 | 3-4 小時 |
| 4 | 圖片/文件分析 | 視覺能力 | VISION-01~04 | 2-3 小時 |
| 5 | 生圖降級鏈 | 智慧生圖 A→B→C | IMG-01~05 | 3-4 小時 |
| 6 | 部署上線 | Render 正式上線 | DEPLOY-01~03 | 1-2 小時 |

---

## Phase 1：環境準備

**Goal:** 所有帳號申請完成，本機開發環境就緒，可以開始寫程式

**Success Criteria:**
1. LINE Bot Channel 建立完成，有 Channel Access Token 和 Channel Secret
2. Gemini API Key 申請完成，可在 Python 呼叫
3. Supabase 專案建立，資料庫連線字串取得
4. ngrok 安裝完成，可以產生公開 HTTPS URL
5. Python 環境（3.11+）安裝，`pip install` 可用

**步驟：**
- [ ] 前往 [LINE Developers](https://developers.line.biz/) 登入
- [ ] 建立 Provider → 建立 Messaging API Channel
- [ ] 取得 Channel Access Token（長期）和 Channel Secret
- [ ] 前往 [Google AI Studio](https://aistudio.google.com/) 申請 Gemini API Key
- [ ] 前往 [Supabase](https://supabase.com/) 建立新專案
- [ ] 記錄 Supabase URL 和 anon key
- [ ] 安裝 [ngrok](https://ngrok.com/) 並取得 authtoken
- [ ] 確認 Python 3.11+ 已安裝（`python --version`）

---

## Phase 2：基本對話 Bot（最小可運作版）

**Goal:** 用戶在 LINE 傳訊息，Bot 用 Gemini 回覆 — 最簡單的版本先跑起來

**Success Criteria:**
1. FastAPI 在本地 8000 port 啟動
2. ngrok 將本地 8000 port 暴露為 HTTPS URL
3. LINE Webhook 設定為 ngrok URL，驗證通過
4. 使用者在 LINE 傳「你好」，Bot 在 3 秒內回覆 Gemini 的答案
5. LINE Webhook 簽名驗證正常運作（防偽造請求）

**檔案結構：**
```
LINEBOT/
├── main.py          ← FastAPI 主程式
├── gemini_client.py ← Gemini 呼叫封裝
├── line_handler.py  ← LINE 訊息處理
├── requirements.txt ← 套件清單
└── .env             ← API Keys（不上 git）
```

**核心套件：**
```
fastapi
uvicorn
line-bot-sdk
google-generativeai
python-dotenv
```

---

## Phase 3：Gemini Agent + 長期記憶 + 網路搜尋

**Goal:** Bot 有工具呼叫能力，能記住你說過的話，能幫你查網路

**Success Criteria:**
1. Gemini 以 Agent 模式運作（Function Calling 啟用）
2. 使用者說「記得我喜歡喝咖啡」，下次對話 Bot 記得
3. 使用者問「今天台灣天氣」，Bot 呼叫搜尋工具並回覆真實資料
4. Supabase memories 資料表有正確寫入/讀取
5. 記憶在重開 Bot 後仍然存在（跨 session）

**Supabase 資料表：**
```sql
CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category TEXT,        -- 'preference' | 'project' | 'conversation'
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**工具清單：**
```python
tools = [
  search_web(query: str) -> str,
  save_memory(category: str, content: str) -> str,
  load_memories(query: str) -> list[str],
]
```

---

## Phase 4：圖片/文件分析

**Goal:** 使用者可以傳圖片或 PDF，Bot 看懂並回覆分析

**Success Criteria:**
1. 使用者傳照片，Bot 能描述圖片內容
2. 使用者傳 PDF，Bot 能摘要文件重點
3. 使用者傳截圖問「這個錯誤是什麼意思」，Bot 能解釋
4. 圖片下載、分析、回覆全流程在 10 秒內完成

**實作重點：**
- LINE 圖片訊息需用 Token 下載（有時效性）
- PDF 解析用 `pypdf` 套件
- Gemini Vision 支援直接傳 bytes

---

## Phase 5：生圖降級鏈

**Goal:** 使用者說「幫我畫一隻貓」，Bot 自動找免費服務生圖並回傳

**Success Criteria:**
1. 偵測到生圖意圖，呼叫 Provider A
2. Provider A 失敗時（HTTP 429/500），自動切換 Provider B
3. Provider B 失敗時，自動切換 Provider C
4. 全部失敗時，回覆「今日免費額度已用完，請明天再試」
5. 成功生圖後，圖片透過 LINE 回傳給使用者

**Provider 研究清單（待研究階段確認優先順序）：**
| Provider | 服務 | 免費額度 |
|---------|------|---------|
| A | Gemini Imagen 3（Google） | 待確認 |
| B | Stability AI / Replicate | 待確認 |
| C | Hugging Face Inference API | 每月固定額度 |

**降級邏輯：**
```python
async def generate_image_with_fallback(prompt: str) -> bytes:
    providers = [provider_a, provider_b, provider_c]
    for provider in providers:
        try:
            result = await provider.generate(prompt)
            if result:
                return result
        except QuotaExceededError:
            continue
    raise AllProvidersExhaustedError("今日免費額度已用完")
```

---

## Phase 6：部署上線

**Goal:** Bot 從 ngrok 本地測試遷移至 Render.com，24/7 可用

**Success Criteria:**
1. Render Web Service 建立，程式碼從 GitHub 自動部署
2. 所有環境變數在 Render 設定完成
3. LINE Webhook URL 改為 Render URL，驗證通過
4. 使用者在 LINE 傳訊息，Bot 正常回覆（非 ngrok）
5. 了解 Render 免費層睡眠機制（15 分鐘閒置後睡眠，第一則訊息會慢）

**注意：Render 免費層限制**
- 閒置 15 分鐘後進入睡眠
- 收到第一則訊息需 20-30 秒喚醒
- 解法：用 cron job 每 14 分鐘 ping 一次（保持喚醒）

---

## 資料夾結構（Phase 6 完成後）

```
LINEBOT/
├── .planning/            ← GSD 規劃文件
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   └── STATE.md
├── app/
│   ├── main.py           ← FastAPI 入口
│   ├── line_handler.py   ← LINE 事件處理
│   ├── gemini_agent.py   ← Gemini Agent + Tools
│   ├── memory.py         ← Supabase 記憶讀寫
│   ├── search.py         ← 網路搜尋工具
│   ├── vision.py         ← 圖片/PDF 分析
│   └── image_gen.py      ← 生圖降級鏈
├── .env                  ← API Keys（不上 git）
├── .env.example          ← 環境變數範本（上 git）
├── .gitignore
├── requirements.txt
├── Dockerfile            ← Render 部署用
└── README.md
```

---

## 環境變數清單（.env）

```env
# LINE
LINE_CHANNEL_ACCESS_TOKEN=xxx
LINE_CHANNEL_SECRET=xxx

# Gemini
GEMINI_API_KEY=xxx

# Supabase
SUPABASE_URL=xxx
SUPABASE_ANON_KEY=xxx

# 搜尋（選一）
GOOGLE_SEARCH_API_KEY=xxx
GOOGLE_SEARCH_ENGINE_ID=xxx

# 生圖 Provider B（選填）
STABILITY_API_KEY=xxx
REPLICATE_API_TOKEN=xxx
```

---

*Last updated: 2026-06-02 — 初始化*
