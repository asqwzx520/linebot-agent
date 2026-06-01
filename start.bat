@echo off
echo ========================================
echo  LINE Bot AI Agent - 本地啟動
echo ========================================
echo.

REM 檢查 .env 是否存在
if not exist .env (
    echo [錯誤] 找不到 .env 檔案！
    echo 請先複製 .env.example 為 .env 並填入 API Keys
    pause
    exit /b 1
)

echo [1/2] 啟動 FastAPI 伺服器（port 8000）...
start "FastAPI - LINE Bot" cmd /k "cd /d %~dp0 && uvicorn app.main:app --reload --port 8000"

echo 等待伺服器啟動...
timeout /t 3 /nobreak > nul

echo [2/2] 啟動 ngrok 通道...
start "ngrok - 公開 URL" cmd /k "ngrok http 8000"

echo.
echo ========================================
echo 啟動完成！
echo.
echo 接下來：
echo 1. 看 ngrok 視窗，複製 https://xxxx.ngrok-free.app 網址
echo 2. 到 LINE Developers 貼上 Webhook URL（加上 /webhook）
echo    例如：https://xxxx.ngrok-free.app/webhook
echo 3. 點 Verify 驗證，打開 Use webhook
echo 4. 用 LINE 傳訊息測試！
echo ========================================
pause
