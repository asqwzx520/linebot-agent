# Project State — LINE Bot AI 個人助理

## Current Status

- **Phase:** 0（規劃完成，尚未開始實作）
- **Last Updated:** 2026-06-02
- **Next Action:** 開始 Phase 1 — 環境準備

## Phase Progress

| Phase | 名稱 | 狀態 |
|-------|------|------|
| 1 | 環境準備 | ⬜ 未開始 |
| 2 | 基本對話 Bot | ⬜ 未開始 |
| 3 | Agent + 記憶 + 搜尋 | ⬜ 未開始 |
| 4 | 圖片/文件分析 | ⬜ 未開始 |
| 5 | 生圖降級鏈 | ⬜ 未開始 |
| 6 | 部署上線 | ⬜ 未開始 |

## Decisions Log

| 日期 | 決策 | 原因 |
|------|------|------|
| 2026-06-02 | 使用 Gemini 1.5 Flash | 有免費層、支援圖片、支援 Function Calling |
| 2026-06-02 | 使用 Supabase 做記憶庫 | 免費 PostgreSQL，不需自架 |
| 2026-06-02 | ngrok 先測試，Render 後部署 | 初學者友善，先本地跑通 |
| 2026-06-02 | 生圖用降級鏈 A→B→C | 額度耗盡自動切換，不中斷服務 |
| 2026-06-02 | 生影片列為 v2 | v1 先穩固核心功能 |

## Open Questions

- [ ] 生圖 Provider A/B/C 的具體免費額度為何？（待研究確認）
- [ ] 搜尋工具用 Google Custom Search API 或其他方案？
- [ ] Supabase 記憶是否需要向量搜尋（embedding）？
