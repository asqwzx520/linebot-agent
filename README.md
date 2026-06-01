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
