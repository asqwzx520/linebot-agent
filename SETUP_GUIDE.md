# 🤖 LINE Bot AI Agent — 完整安裝教學（直接上線版）

> 初學者友善，每一步都有說明。  
> 預計花費時間：**60-90 分鐘**  
> 不需要 ngrok，直接部署到雲端！

---

## 📋 需要的帳號（全部免費）

| 服務 | 用途 | 網址 |
|------|------|------|
| LINE Developers | 建立 Bot | https://developers.line.biz/ |
| Google AI Studio | Gemini API Key | https://aistudio.google.com/ |
| Supabase | 長期記憶資料庫 | https://supabase.com/ |
| GitHub | 存放程式碼 | https://github.com/ |
| Render.com | 雲端伺服器 | https://render.com/ |

---

## 🔧 Step 1：安裝 Git

1. 前往 https://git-scm.com/download/win
2. 下載並安裝（全部按 Next 即可）
3. 安裝完後，開啟「命令提示字元」（Win + R → 輸入 cmd → Enter）
4. 輸入 `git --version` → 看到版本號代表成功

---

## 📱 Step 2：建立 LINE Bot

1. 前往 https://developers.line.biz/
2. 用你的 **LINE 帳號**登入
3. 點「**Create a new provider**」→ 輸入任意名稱（如「我的AI助理」）→ Create
4. 點「**Create a new channel**」→ 選「**Messaging API**」
5. 填寫：
   - Channel name：Bot 名稱（例如「AI助理」）
   - Channel description：隨意
   - Category / Subcategory：隨意選
   - Email：你的 email
6. 同意條款 → Create
7. 進入 Channel → 點上方「**Messaging API**」分頁
8. 滾到「**Channel access token**」→ 點「**Issue**」→ 複製這串文字 ✏️
9. 點上方「**Basic settings**」分頁 → 找「**Channel secret**」→ 複製 ✏️

> 📝 先把這兩個值貼到記事本備用

---

## 🤖 Step 3：取得 Gemini API Key

1. 前往 https://aistudio.google.com/
2. 用 **Google 帳號**登入
3. 點左側「**Get API key**」→「**Create API key**」
4. 複製 API Key ✏️

> ℹ️ 本專案使用 **Gemini 3.5 Flash** 作為主力模型，搭配 3.1-flash / 3.1-flash-lite 作為備用降級鏈。

---

## 🗄️ Step 4：建立 Supabase 資料庫

### 4.1 建立帳號與專案
1. 前往 https://supabase.com/ → 點「**Start your project**」→ 用 GitHub 或 Email 註冊
2. 點「**New project**」：
   - Name：`linebot-db`
   - Database Password：設一個密碼（記下來）
   - Region：選「**Southeast Asia (Singapore)**」
3. 點「**Create new project**」→ 等待約 1-2 分鐘

### 4.2 取得連線資訊
1. 點左側齒輪「**Project Settings**」→「**API**」
2. 複製「**Project URL**」（形如 `https://xxxx.supabase.co`）✏️
3. 複製「**anon / public**」key ✏️
4. 複製「**service_role**」key ✏️（在同一頁面，請妥善保管，勿公開）

### 4.3 建立資料表
1. 點左側「**SQL Editor**」
2. 點「**New query**」
3. 打開資料夾 `C:\Users\User\Desktop\ClaudeProject\LINEBOT\setup_supabase.sql`
4. 全選複製內容 → 貼到 SQL Editor
5. 點右上角「**Run**」→ 看到 Success ✅

> ⚠️ **安全注意事項：** 如果你之前曾設定過「allow_all」的 RLS（Row Level Security）policy，請務必將其 **DROP 掉**，改用 service_role key 存取資料庫。保留 allow_all policy 會讓任何人都能讀寫你的資料。執行以下 SQL 刪除舊的開放 policy：
> ```sql
> DROP POLICY IF EXISTS "allow_all" ON memories;
> DROP POLICY IF EXISTS "allow_all" ON conversations;
> ```
> 本專案透過後端的 `SUPABASE_SERVICE_ROLE_KEY` 繞過 RLS，因此不需要開放 policy。

### 4.4 建立圖片儲存空間
1. 點左側「**Storage**」
2. 點「**New bucket**」
3. Bucket name：`images`
4. **⚠️ 勾選「Public bucket」**（重要！）
5. 點「**Save**」✅

---

## 🐙 Step 5：上傳程式碼到 GitHub

### 5.1 建立 GitHub 帳號
1. 前往 https://github.com/ → 點「**Sign up**」→ 免費註冊

### 5.2 建立 Repository
1. 登入後，點右上角「**+**」→「**New repository**」
2. Repository name：`linebot-agent`
3. 選「**Private**」（私人，只有你看得到）
4. **不要**勾選 Initialize this repository
5. 點「**Create repository**」

### 5.3 上傳程式碼
1. 打開命令提示字元，輸入（把 `你的帳號` 換成你的 GitHub 帳號名稱）：

```
cd C:\Users\User\Desktop\ClaudeProject\LINEBOT
git remote add origin https://github.com/你的帳號/linebot-agent.git
git push -u origin master
```

2. 會彈出 GitHub 登入視窗 → 登入
3. 看到 `master -> master` 代表上傳成功 ✅

---

## ☁️ Step 6：部署到 Render

### 6.1 建立帳號
1. 前往 https://render.com/ → 點「**Get Started for Free**」
2. 用 GitHub 帳號登入（方便連接 repo）

### 6.2 建立 Web Service
1. 點「**New +**」→「**Web Service**」
2. 選「**Connect a repository**」→ 選剛才建立的 `linebot-agent`
3. 設定：
   - **Name**：`linebot-agent`（或任意）
   - **Region**：Singapore
   - **Branch**：master
   - **Runtime**：Python 3
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**：選「**Free**」

### 6.3 設定環境變數（重要！）
1. 滾到「**Environment Variables**」區塊
2. 逐一點「**Add Environment Variable**」，填入：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | 你的 Channel Access Token |
| `LINE_CHANNEL_SECRET` | 你的 Channel Secret |
| `GEMINI_API_KEY` | 你的 Gemini API Key |
| `SUPABASE_URL` | 你的 Supabase Project URL |
| `SUPABASE_ANON_KEY` | 你的 Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | 你的 Supabase service_role key（Step 4.2 取得）|

> ⚠️ `SUPABASE_SERVICE_ROLE_KEY` 具有完整資料庫存取權限，請勿提交到 GitHub。只在 Render 環境變數中設定。

### 6.4 部署
1. 點「**Create Web Service**」
2. 等待部署（約 3-5 分鐘），看 log 出現 `Uvicorn running` 代表成功 ✅
3. 複製頁面頂端的網址：`https://linebot-agent-xxxx.onrender.com` ✏️

---

## 📡 Step 7：設定 LINE Webhook

1. 回到 https://developers.line.biz/
2. 進入你的 Channel → 點「**Messaging API**」分頁
3. 找到「**Webhook URL**」
4. 填入：`https://linebot-agent-xxxx.onrender.com/webhook`
   （換成你的 Render 網址）
5. 點「**Update**」
6. 點「**Verify**」→ 看到 **Success** ✅
7. 確認「**Use webhook**」是開啟狀態 ✅

### 關閉自動回覆（避免干擾）
1. 同一頁面，找「**Auto-reply messages**」→ 點「**Edit**」
2. 關閉「Auto-reply」和「Greeting messages」

---

## 💬 Step 8：測試 Bot！

1. 在 Messaging API 頁面找到「**Bot's QR code**」
2. 用 LINE 掃描 → 加入好友
3. 傳訊息測試：

```
你好                      → 基本對話
今天台灣天氣如何？           → 搜尋網路
幫我記住我喜歡喝咖啡          → 儲存記憶
你記得什麼？                → 讀取記憶
幫我畫一隻橘色的貓            → 生成圖片
（傳一張圖片）              → 圖片分析
（傳一份 PDF）             → 文件分析
```

---

## 👥 多用戶支援說明

本 Bot 支援多位用戶同時使用，每位用戶的記憶**完全隔離**：

- 記憶、對話記錄以 LINE 的 `user_id` 為索引儲存在 Supabase
- 用戶 A 的記憶不會洩漏給用戶 B
- 無需任何額外設定，多用戶隔離預設啟用

---

## 🛡️ 速率限制

為防止濫用，每位用戶的請求頻率有以下限制：

- **上限：每分鐘 10 則訊息**（per user）
- 超過限制時，Bot 會回覆提示訊息，請稍後再試
- 限制以 LINE `user_id` 為單位，不同用戶互不影響

---

## ⚠️ Render 免費版注意事項

- 15 分鐘沒人用，服務會「睡眠」
- 睡眠後第一則訊息需等 **20-30 秒** 才有回應（之後就正常了）
- 對個人使用來說完全夠用

---

## ❓ 常見問題

**Q: git push 時要求輸入帳號密碼**  
A: 輸入你的 GitHub 帳號名稱和密碼（或 Personal Access Token）

**Q: Render 部署失敗**  
A: 點「Logs」查看錯誤，通常是環境變數沒填或填錯

**Q: LINE Webhook Verify 失敗**  
A: 確認 Render 部署成功、網址正確加上 `/webhook`

**Q: Bot 沒有回覆**  
A: 到 Render Dashboard 看 Logs，把錯誤訊息截圖給 Claude

**Q: 圖片沒有顯示**  
A: 確認 Supabase Storage 有建立 `images` bucket 且設為 Public

---

## 🔄 之後更新程式碼

每次程式碼有更動，只需要：
```
cd C:\Users\User\Desktop\ClaudeProject\LINEBOT
git add -A
git commit -m "更新說明"
git push
```
Render 會自動偵測並重新部署！

---

*遇到任何問題，把錯誤訊息截圖給 Claude，我幫你解決。*
