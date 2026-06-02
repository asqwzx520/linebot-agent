# 🚀 LINE Bot AI 助理 — V2 功能規劃

> 文件建立：2026-06-03  
> 當前版本：v1.0（已上線）  
> 下一版本：v2.0

---

## ✅ V1 已完成功能

| 功能 | 狀態 | 說明 |
|------|------|------|
| 基本對話 | ✅ 上線 | Gemini 3.5 Flash 主力模型 |
| 網路搜尋 | ✅ 上線 | DuckDuckGo，無需 API Key |
| 長期記憶 | ✅ 上線 | Supabase 永久儲存，user_id 隔離 |
| 圖片分析 | ✅ 上線 | Gemini Vision 多模態 |
| PDF 分析 | ✅ 上線 | pypdf 解析，最多 20 頁 |
| AI 生圖 | ✅ 上線 | Pollinations FLUX → HF SDXL → Turbo 降級鏈 |
| 多模型備用 | ✅ 上線 | 3.5-flash → 3.1-flash → 3.1-flash-lite |
| 多 API Key | ✅ 上線 | 最多 3 個帳號各自額度 |
| 多用戶隔離 | ✅ 上線 | 每人記憶完全分開 |
| 雲端部署 | ✅ 上線 | Render.com Docker，GitHub 自動部署 |

---

## 🗺️ V2 功能規劃總覽

```
V2.0 目標：讓 Bot 從「會聊天」升級成「真正的個人助理」
```

| # | 功能 | 難度 | 優先度 | 預估工時 |
|---|------|------|--------|---------|
| 1 | 🗣️ 語音訊息 | ⭐⭐ | 🔴 高 | 1-2 天 |
| 2 | 📊 Excel 數據分析 | ⭐⭐ | 🔴 高 | 1-2 天 |
| 3 | 📅 Google 日曆整合 | ⭐⭐⭐ | 🟡 中 | 3-5 天 |
| 4 | 🎬 影片生成 | ⭐⭐⭐⭐ | 🟡 中 | 5-7 天 |

---

## 📋 各功能詳細規劃

---

### 🗣️ 功能 1：語音訊息

**目標：** 用戶傳語音給 Bot，Bot 理解後文字回覆；或可選語音回覆。

#### 技術方案

```
用戶傳語音 (LINE 語音訊息 .m4a)
       │
       ▼
下載音訊檔案
       │
       ▼
語音轉文字 (STT)
  主要：Gemini 1.5 Flash Audio（免費，支援中文）
  備用：OpenAI Whisper（需 API Key）
       │
       ▼
轉成文字 → 原有文字處理流程 (gemini_agent.process_text)
       │
       ▼
文字回覆（基本）
  或
文字轉語音 (TTS)（進階，可選）
  方案：Google Cloud TTS / ElevenLabs
```

#### 需要的 API / 服務

| 服務 | 用途 | 費用 |
|------|------|------|
| Gemini Audio API | 語音轉文字（STT） | 免費（含在 Gemini 額度） |
| Google Cloud TTS | 文字轉語音（TTS）| 免費 100 萬字/月 |

#### 程式碼修改點

- `app/line_handler.py` — 新增 `AudioMessageContent` 處理
- `app/gemini_agent.py` — 新增 `process_audio()` 函數
- `app/tts.py` — 新建，文字轉語音邏輯（可選）
- `requirements.txt` — 新增 `google-cloud-texttospeech`

#### 實作步驟

```
1. line_handler.py 加入 AudioMessageContent 偵測
2. 下載音訊 → 轉 base64 → 送 Gemini Audio
3. 取得文字 → 走原有 process_text 流程
4. （可選）回覆語音：TTS → 上傳 Supabase Storage → 發 AudioMessage
```

---

### 📊 功能 2：Excel / CSV 數據分析

**目標：** 用戶傳 Excel 或 CSV 檔案，Bot 自動分析並給出洞察。

#### 技術方案

```
用戶傳 .xlsx / .csv 檔案
       │
       ▼
下載並解析（pandas + openpyxl）
       │
       ▼
自動生成數據摘要：
  - 欄位名稱、資料型別
  - 基本統計（平均、最大、最小、空值數）
  - 前 10 筆資料
       │
       ▼
摘要 + 用戶問題 → Gemini 分析
       │
       ▼
回覆：分析結果 + 建議
  可選：用 matplotlib 生成圖表 → 回覆圖片
```

#### 需要的 API / 服務

| 服務 | 用途 | 費用 |
|------|------|------|
| pandas | 資料分析 | 免費 |
| openpyxl | 讀取 Excel | 免費 |
| matplotlib | 生成圖表（可選）| 免費 |

#### 程式碼修改點

- `app/line_handler.py` — 擴充 FileMessageContent，支援 `.xlsx` / `.csv`
- `app/gemini_agent.py` — 新增 `process_excel()` 函數
- `app/data_analyzer.py` — 新建，pandas 分析邏輯
- `requirements.txt` — 新增 `pandas openpyxl matplotlib`

#### 示例對話

```
用戶傳：sales_2026.xlsx

Bot 回覆：
📊 檔案分析完成！

📁 基本資訊
• 共 1,234 筆資料，8 個欄位
• 欄位：日期、產品、地區、銷售額、數量、客戶、業務員、備註

📈 銷售摘要
• 總銷售額：$2,456,789
• 平均每筆：$1,991
• 最高單筆：$45,000（2026/03/15，產品A）
• 最低單筆：$120

🔍 洞察
1. 北區銷售額佔總體 42%，表現最佳
2. 3月份有明顯高峰，建議分析原因
3. 有 23 筆資料的「地區」欄位為空值

你想進一步分析哪個部分？
```

---

### 📅 功能 3：Google 日曆整合

**目標：** 透過對話管理 Google 日曆，新增/查詢/修改行程。

#### 技術方案

```
用戶說：「明天下午3點幫我加一個『開會』的行程」
       │
       ▼
Gemini 理解意圖 → 呼叫 calendar_add 工具
       │
       ▼
Google Calendar API（OAuth 2.0）
  - 新增行程
  - 查詢行程
  - 修改行程
  - 刪除行程
       │
       ▼
確認回覆給用戶
```

#### 需要的 API / 服務

| 服務 | 用途 | 費用 |
|------|------|------|
| Google Calendar API | 日曆操作 | 免費 |
| Google OAuth 2.0 | 授權登入 | 免費 |

#### OAuth 流程設計

```
首次使用：
1. 用戶傳「連結我的 Google 日曆」
2. Bot 回覆授權連結
3. 用戶點擊，授權 Google 帳號
4. Token 儲存到 Supabase（依 user_id）

之後每次：直接使用儲存的 Token 操作日曆
```

#### 新增 Supabase 資料表

```sql
CREATE TABLE google_tokens (
    user_id      TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

#### 程式碼修改點

- `app/calendar_tool.py` — 新建，Google Calendar API 封裝
- `app/oauth.py` — 新建，OAuth 2.0 流程
- `app/gemini_agent.py` — 新增 4 個日曆工具函數
- `app/main.py` — 新增 `/oauth/callback` 路由

#### 示例對話

```
用戶：明天下午3點到5點有個跟客戶的會議
Bot：✅ 已新增行程！
     📅 明天（2026/06/04）15:00 - 17:00
     📌 與客戶會議
     需要設定提醒嗎？

用戶：這週有什麼行程？
Bot：📅 本週行程（06/03 - 06/09）
     • 週三 15:00 與客戶會議
     • 週五 10:00 團隊週報
     共 2 個行程
```

---

### 🎬 功能 4：AI 影片生成

**目標：** 用戶輸入描述，Bot 生成短影片。

#### 技術方案

```
用戶說：「幫我生成一個海浪拍打礁石的影片」
       │
       ▼
Gemini 將描述優化為英文 prompt
       │
       ▼
影片生成降級鏈：
  A: Kling AI（科大訊飛，中文友善，免費額度）
  B: Runway Gen-4（高品質，有免費試用）
  C: Pika Labs（有免費額度）
  D: HuggingFace Video Models（完全免費，品質較低）
       │
       ▼
下載影片 → 上傳 Supabase Storage
       │
       ▼
透過 LINE 傳送影片訊息
```

#### 各平台比較

| 平台 | 免費額度 | 影片長度 | 品質 | API |
|------|---------|---------|------|-----|
| Kling AI | 166 credits/月 | 5 秒 | ⭐⭐⭐⭐⭐ | ✅ 有 |
| Runway Gen-4 | 125 credits | 5-10 秒 | ⭐⭐⭐⭐⭐ | ✅ 有 |
| Pika Labs | 有免費額度 | 3-5 秒 | ⭐⭐⭐⭐ | ✅ 有 |
| HuggingFace | 無限（排隊） | 2-4 秒 | ⭐⭐ | ✅ 有 |

#### 挑戰

- 影片生成耗時 30 秒 ~ 3 分鐘（LINE Webhook 有逾時限制）
- 需要**非同步排隊機制**：收到請求 → 回覆「生成中」→ 完成後主動推播

#### 非同步架構

```
用戶請求生圖
     │
     ▼
立即回覆「影片生成中，約需 1-3 分鐘...」
     │
     ▼
背景 Task（Render Background Worker 或 Cron）
     │
     ▼
輪詢影片生成狀態
     │
     ▼
完成 → 主動推播給用戶（Push Message API）
```

#### 程式碼修改點

- `app/video_gen.py` — 新建，影片生成降級鏈
- `app/gemini_agent.py` — 新增 `video_generate` 工具
- `app/main.py` — 背景任務處理
- `requirements.txt` — 新增各平台 SDK

---

## 🗓️ 建議實作順序

```
Phase 1（最快上線，1-2 週）
├── 🗣️ 語音訊息    ← 最常用，技術最簡單
└── 📊 數據分析    ← 商業價值高

Phase 2（中期，3-4 週）
└── 📅 Google 日曆  ← 需要 OAuth，稍複雜

Phase 3（長期，1-2 月）
└── 🎬 影片生成    ← 需要非同步架構，最複雜
```

---

## 🔧 V2 技術債 / 需要補強

| 項目 | 說明 | 優先度 |
|------|------|--------|
| 錯誤追蹤 | 接入 Sentry，線上錯誤即時通知 | 🟡 中 |
| 用戶設定 | `/設定` 指令（語言、通知、偏好）| 🟡 中 |
| 管理面板 | 查看用戶數、訊息量、記憶使用量 | 🟢 低 |
| 對話匯出 | 用戶可匯出自己的對話記錄 | 🟢 低 |
| 記憶容量限制 | 防止單一用戶儲存過多記憶 | 🟡 中 |
| 速率限制 | 防止單一用戶短時間大量請求 | 🟡 中 |

---

## 💰 V2 費用預估（月）

> 假設 10-50 位活躍用戶

| 服務 | 免費額度 | 超過後費用 |
|------|---------|-----------|
| LINE Messaging API | 500 則/月 | NT$1 / 100 則 |
| Gemini API | 1500 req/天 | 超過需升級 |
| Supabase | 500 MB | 超過 $25/月 |
| Render | 750 小時/月 | $7/月升 Starter |
| Google Calendar | 免費 | - |
| Kling AI 影片 | 166 credits/月 | $10/月 起 |
| Runway 影片 | 125 credits | $15/月 起 |

**預估：個人使用完全免費；50人以上月費約 NT$500-1500**

---

## 📝 開發規範

- 所有新功能必須有 **降級機制**（主要失敗 → 備用 → 友善錯誤訊息）
- 所有 API 呼叫必須有 **超時設定**（不超過 LINE Webhook 15 秒限制）
- 耗時操作（>5 秒）必須使用 **非同步 + 主動推播** 架構
- 所有用戶資料必須依 **user_id 隔離**
- 新增功能前先更新此文件

---

*最後更新：2026-06-03*
