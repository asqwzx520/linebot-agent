# LINE Bot AI 個人助理

個人使用的 LINE Bot，整合 Google Gemini Agent，具備長期記憶、網路搜尋、圖片分析、生圖降級鏈。

## 功能

- 基本 AI 對話（Gemini 1.5 Flash）
- 長期記憶（記住你說過的事）
- 網路搜尋（幫你查資料）
- 圖片/PDF 分析（視覺理解）
- 生圖（免費降級鏈 A→B→C）

## 技術棧

- Python 3.11 + FastAPI
- Google Gemini 1.5 Flash
- LINE Messaging API
- Supabase（長期記憶）
- Render.com（部署）

## 環境設定

複製 `.env.example` 為 `.env` 並填入 API Keys：

```bash
cp .env.example .env
```

## 安裝

```bash
pip install -r requirements.txt
```

## 本地測試

```bash
# 啟動 FastAPI
uvicorn app.main:app --reload --port 8000

# 另開終端，啟動 ngrok
ngrok http 8000
```

將 ngrok 的 HTTPS URL 設定為 LINE Bot 的 Webhook URL。

## 部署

詳見 `.planning/ROADMAP.md` Phase 6。

---

<!-- generated-by: gsd-doc-writer -->

## 目前使用的模型（更新）

實際模型降級鏈（`app/gemini_agent.py`）：

| 優先順序 | 模型 | 說明 |
|---|---|---|
| 1 | `gemini-3.5-flash` | 主力模型，最高品質 |
| 2 | `gemini-3.1-flash` | 第二備用 |
| 3 | `gemini-3.1-flash-lite` | 高 RPM 備用（額度較寬鬆） |

> 注意：技術棧欄位所列的 `Gemini 1.5 Flash` 為舊版紀錄，目前實際使用 `gemini-3.5-flash` 為首選。

## 架構概覽

```
LINE Messaging API
        │  webhook POST /webhook
        ▼
app/main.py  (FastAPI 入口，驗證 X-Line-Signature)
        │
        ▼
app/line_handler.py  (事件路由：文字 / 圖片 / PDF)
        │
        ├─► app/rate_limiter.py   (滑動視窗速率限制，每用戶 10 則/60 秒)
        │
        ▼
app/gemini_agent.py  (Gemini 模型 × API Key 降級鏈)
        │
        ├─► app/memory.py         (Supabase 長期記憶 + 對話歷史)
        ├─► app/search.py         (DuckDuckGo 網路搜尋)
        └─► app/image_gen.py      (生圖降級鏈 A→B→C)
                ├─► Pollinations FLUX   (免費，無需 Key)
                ├─► HuggingFace SDXL   (需 HF_TOKEN)
                └─► Pollinations Turbo  (備用)
```

生成的圖片會上傳至 Supabase Storage，取得穩定公開 URL 後傳回 LINE。

## 安全機制

- **速率限制**：`app/rate_limiter.py` 使用記憶體滑動視窗，每個 LINE 用戶每 60 秒最多 10 則訊息，超過則拒絕。
- **多用戶記憶隔離**：所有 Supabase 查詢均以 `user_id`（LINE userId）過濾，不同用戶的記憶與對話紀錄完全分開。
- **service_role key**：後端使用 `SUPABASE_SERVICE_ROLE_KEY` 存取 Supabase，繞過 RLS 以確保伺服器端完整控制；`SUPABASE_ANON_KEY` 為向下相容備用，不直接暴露給前端。
- **Prompt Injection 防護**：`memory_save` 工具限制 content 最長 500 字元、category 最長 50 字元，並以白名單驗證分類；記憶內容以 XML 標記（`<user_memories>`）與用戶輸入結構化分隔。
- **Webhook 簽章驗證**：`app/main.py` 使用 `linebot.v3.WebhookParser` 驗證 `X-Line-Signature`，拒絕偽造請求。

## 多 API Key 降級機制

可設定最多三組不同 Google 帳號的 Gemini API Key，各自享有獨立的免費額度：

```
GEMINI_API_KEY=...    # 必填
GEMINI_API_KEY_2=...  # 選填
GEMINI_API_KEY_3=...  # 選填
```

降級順序為 `Key1+3.5-flash → Key2+3.5-flash → Key3+3.5-flash → Key1+3.1-flash → ...`，遇到 `ResourceExhausted`（額度耗盡）或 `ServiceUnavailable` 時自動切換，所有組合皆失敗才回傳錯誤。

## 環境變數

| 變數 | 必填 | 說明 |
|---|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | 必填 | LINE Developers Console 取得 |
| `LINE_CHANNEL_SECRET` | 必填 | LINE Developers Console 取得 |
| `GEMINI_API_KEY` | 必填 | Google AI Studio 取得 |
| `GEMINI_API_KEY_2` | 選填 | 第二組 Gemini Key（不同 Google 帳號） |
| `GEMINI_API_KEY_3` | 選填 | 第三組 Gemini Key（不同 Google 帳號） |
| `SUPABASE_URL` | 必填 | Supabase 專案 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | 建議填 | 後端完整存取權（繞過 RLS） |
| `SUPABASE_ANON_KEY` | 選填 | 向下相容備用（若未設定 service_role） |
| `HF_TOKEN` | 選填 | Hugging Face token，啟用 SDXL 生圖備用 |
| `PORT` | 選填 | 服務埠（預設 `8000`） |

## 快速測試指令

```bash
# 健康檢查（確認服務正在運行）
curl http://localhost:8000/

# 模擬 webhook（需有效 X-Line-Signature，僅供整合測試）
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: <signature>" \
  -d '{"destination":"","events":[]}'
```
