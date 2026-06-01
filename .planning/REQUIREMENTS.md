# Requirements — LINE Bot AI 個人助理

## v1 Requirements

### 核心對話（CORE）

- [ ] **CORE-01** 使用者傳文字訊息，Bot 呼叫 Gemini 並回覆
- [ ] **CORE-02** Bot 維持對話上下文（同一 session 內記得前幾句）
- [ ] **CORE-03** Webhook 簽名驗證（防止假冒 LINE 的請求）

### 長期記憶（MEM）

- [ ] **MEM-01** 使用者說的個人偏好自動存入 Supabase
- [ ] **MEM-02** 使用者的專案/工作進度可儲存與查詢
- [ ] **MEM-03** 重要對話內容自動摘要存入記憶庫
- [ ] **MEM-04** 每次對話開始前，自動載入相關記憶作為 Gemini 的 context
- [ ] **MEM-05** 使用者可指令刪除特定記憶（「忘記XXX」）

### 網路搜尋（SEARCH）

- [ ] **SEARCH-01** 偵測到查詢意圖，自動呼叫搜尋工具
- [ ] **SEARCH-02** 搜尋結果摘要後回覆（不直接丟原始 JSON）
- [ ] **SEARCH-03** 標示資料來源（哪個網站）

### 圖片/文件分析（VISION）

- [ ] **VISION-01** 接收 LINE 傳來的圖片並下載
- [ ] **VISION-02** 圖片傳給 Gemini 視覺模型分析
- [ ] **VISION-03** 接收 PDF 文件並解析文字內容
- [ ] **VISION-04** 回覆圖片/文件的分析結果

### 生圖降級鏈（IMG）

- [ ] **IMG-01** 偵測生圖意圖，呼叫 Provider A 生圖
- [ ] **IMG-02** Provider A 失敗/額度耗盡，自動切換 Provider B
- [ ] **IMG-03** Provider B 失敗/額度耗盡，自動切換 Provider C
- [ ] **IMG-04** 全部 Provider 失敗，回覆友善提示（告知明日再試）
- [ ] **IMG-05** 成功生圖後，透過 LINE 回傳圖片

### 部署（DEPLOY）

- [ ] **DEPLOY-01** 本地 ngrok 測試環境可正常運作
- [ ] **DEPLOY-02** 部署至 Render.com 並設定環境變數
- [ ] **DEPLOY-03** LINE Webhook URL 指向 Render，正式上線

---

## v2 Requirements（延後）

- **VIDEO-01** 生影片功能（降級鏈同生圖邏輯）
- **MEM-06** 記憶語意搜尋（向量搜尋，更精準召回相關記憶）
- **MULTI-01** 多語言支援（中英自動偵測）
- **REMIND-01** 設定提醒功能（「明天早上提醒我...」）

---

## Out of Scope（明確排除）

| 排除項目 | 原因 |
|---------|------|
| 付費 API | 本專案全程免費方案 |
| 多用戶 | 個人使用，不需要 |
| Web 管理介面 | v1 只用 LINE 操作 |
| 語音訊息處理 | 複雜度高，非核心需求 |

---

## Traceability（需求對應 Phase）

| 需求 ID | Phase |
|---------|-------|
| CORE-01~03 | Phase 2 |
| MEM-01~05 | Phase 3 |
| SEARCH-01~03 | Phase 3 |
| VISION-01~04 | Phase 4 |
| IMG-01~05 | Phase 5 |
| DEPLOY-01~03 | Phase 6 |

---

*Last updated: 2026-06-02*
