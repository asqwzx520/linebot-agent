# 🤖 LINE Bot AI Agent — 完整安裝教學

> 這份教學是為初學者設計的，每一步都有說明。  
> 預計花費時間：**60-90 分鐘**

---

## 📋 你需要的帳號清單

| 服務 | 用途 | 費用 |
|------|------|------|
| LINE Developers | 建立 Bot | 免費 |
| Google AI Studio | Gemini API Key | 免費 |
| Supabase | 長期記憶資料庫 | 免費 |
| ngrok | 本地測試通道 | 免費 |
| Hugging Face | 備用生圖（可選） | 免費 |

---

## 🔧 Step 1：安裝 Python

1. 開啟瀏覽器，前往 https://python.org/downloads/
2. 點「Download Python 3.11.x」（最新 3.11 版本）
3. 執行安裝程式
4. **⚠️ 重要：安裝時勾選「Add Python to PATH」**
5. 完成後，開啟「命令提示字元」（按 Win + R，輸入 cmd）
6. 輸入 `python --version` → 應該看到 `Python 3.11.x`

---

## 🔧 Step 2：安裝 ngrok

1. 前往 https://ngrok.com/ → 點右上角「Sign up」免費註冊
2. 登入後，點左側「Your Authtoken」
3. 複製你的 authtoken（長串英數字）
4. 前往 https://ngrok.com/download → 下載 Windows 版
5. 解壓縮，把 `ngrok.exe` 放到 `C:\Users\User\Desktop\ClaudeProject\LINEBOT\` 資料夾
6. 開啟命令提示字元，輸入：
   ```
   cd C:\Users\User\Desktop\ClaudeProject\LINEBOT
   ngrok config add-authtoken 你的authtoken
   ```

---

## 📱 Step 3：建立 LINE Bot Channel

1. 前往 https://developers.line.biz/
2. 用你的 LINE 帳號登入
3. 點「Create a new provider」→ 輸入任意名稱（如「我的機器人」）→ 建立
4. 點「Create a new channel」→ 選「Messaging API」
5. 填寫資料：
   - Channel name：你的 Bot 名稱（隨意，例如「AI助理」）
   - Channel description：隨意
   - Category：選任意
   - Email：你的 email
6. 同意條款 → 建立
7. 進入 Channel 後，點「Messaging API」分頁
8. 找到「Channel access token」→ 點「Issue」→ 複製這串 token（**Channel Access Token**）
9. 點「Basic settings」分頁 → 找到「Channel secret」→ 複製（**Channel Secret**）

> 💡 把這兩個值先存到記事本，等等要用

---

## 🤖 Step 4：取得 Gemini API Key

1. 前往 https://aistudio.google.com/
2. 用 Google 帳號登入
3. 點左側「Get API key」→「Create API key」
4. 複製 API Key（**Gemini API Key**）

---

## 🗄️ Step 5：建立 Supabase 資料庫

1. 前往 https://supabase.com/ → 點「Start your project」免費註冊
2. 建立新 Organization（隨意名稱）
3. 點「New project」：
   - Name：linebot-db（或任意名稱）
   - Database Password：設一個密碼（先記下來）
   - Region：選 Southeast Asia（Singapore）最近
4. 等待建立（約 1-2 分鐘）
5. 建立完成後，點左側齒輪「Project Settings」→「API」
6. 複製：
   - **Project URL**（形如 `https://xxxx.supabase.co`）
   - **anon / public** key

### Step 5.2：建立資料表

1. 點左側「SQL Editor」
2. 點「New query」
3. 複製 `setup_supabase.sql` 檔案的全部內容貼上
4. 點「Run」（右上角綠色按鈕）
5. 看到 Success 即完成

### Step 5.3：建立 Storage Bucket（生圖用）

1. 點左側「Storage」
2. 點「New bucket」
3. Bucket name：`images`
4. **勾選「Public bucket」**
5. 點「Save」

---

## 🔑 Step 6：設定 API Keys

1. 在 `C:\Users\User\Desktop\ClaudeProject\LINEBOT\` 資料夾
2. 找到 `.env.example` 檔案
3. 複製一份，命名為 `.env`（注意：只有一個點開頭，沒有副檔名）
   > 如果 Windows 不讓你建立，用記事本開 `.env.example`，另存新檔改名為 `.env`
4. 用記事本打開 `.env`，填入所有值：

```env
LINE_CHANNEL_ACCESS_TOKEN=貼上你的Channel Access Token
LINE_CHANNEL_SECRET=貼上你的Channel Secret
GEMINI_API_KEY=貼上你的Gemini API Key
SUPABASE_URL=貼上你的Supabase Project URL
SUPABASE_ANON_KEY=貼上你的Supabase anon key
HF_TOKEN=（可選，先留空）
```

5. 存檔

---

## 📦 Step 7：安裝 Python 套件

1. 開啟命令提示字元
2. 輸入：
   ```
   cd C:\Users\User\Desktop\ClaudeProject\LINEBOT
   pip install -r requirements.txt
   ```
3. 等待安裝完成（約 2-5 分鐘）

---

## 🚀 Step 8：啟動 Bot（本地測試）

1. 在資料夾中找到 `start.bat`
2. **雙擊執行**
3. 會自動開啟兩個視窗：
   - **FastAPI 視窗**：Bot 的後端程式
   - **ngrok 視窗**：公開網址

4. 看 **ngrok 視窗**，找到這行：
   ```
   Forwarding  https://xxxx-xx-xx-xxx-xx.ngrok-free.app -> http://localhost:8000
   ```
   複製 `https://xxxx-xx-xx-xxx-xx.ngrok-free.app` 這個網址

---

## 📡 Step 9：設定 LINE Webhook

1. 回到 https://developers.line.biz/
2. 進入你的 Channel → 點「Messaging API」分頁
3. 找到「Webhook URL」
4. 填入：`https://你的ngrok網址/webhook`
   例如：`https://abcd-1234.ngrok-free.app/webhook`
5. 點「Update」
6. 點「Verify」→ 應該看到 **Success**
7. 確認「Use webhook」是 **開啟** 狀態

---

## 💬 Step 10：測試 Bot

1. 用 LINE 掃描你的 Bot 的 QR Code（在 Messaging API 分頁可以找到）
2. 加入好友後，傳送「你好」
3. Bot 應該在幾秒內回覆！

### 測試指令

```
你好                    ← 基本對話
今天台灣天氣如何？        ← 搜尋網路
幫我記住我喜歡喝咖啡       ← 儲存記憶
你記得什麼？              ← 讀取記憶
幫我畫一隻橘色的貓         ← 生成圖片
（傳一張圖片）            ← 圖片分析
（傳一份 PDF）           ← 文件分析
```

---

## ☁️ Step 11：正式部署到 Render（讓 Bot 24/7 運作）

> 完成本地測試後再做這步

1. 把程式碼上傳到 GitHub：
   - 註冊 https://github.com/
   - 建立 repository（Private）
   - 上傳 LINEBOT 資料夾（**注意 .env 不要上傳**）

2. 前往 https://render.com/ 免費註冊

3. 點「New +」→「Web Service」

4. 連接你的 GitHub repo

5. 設定：
   - Build Command：`pip install -r requirements.txt`
   - Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - 選擇免費方案

6. 點「Environment」分頁，加入所有環境變數（.env 裡的所有值）

7. 部署完成後，複製 Render 給你的 URL（形如 `https://linebot-xxx.onrender.com`）

8. 回到 LINE Developers，把 Webhook URL 改為：
   `https://linebot-xxx.onrender.com/webhook`

> ⚠️ Render 免費版：15 分鐘沒人用會進入睡眠，第一則訊息需等 20-30 秒喚醒。

---

## ❓ 常見問題

**Q: `start.bat` 執行後 FastAPI 視窗顯示錯誤**  
A: 確認 `.env` 檔案存在且 API Keys 都有填寫

**Q: ngrok 顯示「Invalid authtoken」**  
A: 重新執行 `ngrok config add-authtoken 你的authtoken`

**Q: LINE Webhook Verify 失敗**  
A: 確認 FastAPI 有在運作（看 FastAPI 視窗沒有錯誤），ngrok URL 正確加上 `/webhook`

**Q: Bot 沒有回覆**  
A: 看 FastAPI 視窗的 log，找紅色錯誤訊息

**Q: 圖片沒有顯示**  
A: 確認 Supabase Storage 有建立 `images` bucket 且設為 Public

---

## 📞 需要幫助？

把 FastAPI 視窗的錯誤訊息截圖，告訴 Claude 哪一步出問題。
