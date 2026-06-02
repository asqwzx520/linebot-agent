-- ============================================================
-- LINE Bot AI Agent — Supabase 資料庫初始化
-- 在 Supabase Dashboard → SQL Editor 執行此檔案
-- ============================================================

-- 長期記憶表（含 user_id 隔離）
CREATE TABLE IF NOT EXISTS memories (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    TEXT        NOT NULL DEFAULT 'default',
    category   TEXT        NOT NULL DEFAULT 'general',
    content    TEXT        NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 對話歷史表
CREATE TABLE IF NOT EXISTS conversations (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    TEXT        NOT NULL,
    role       TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT        NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引（加速查詢）
CREATE INDEX IF NOT EXISTS idx_memories_user      ON memories(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_category  ON memories(user_id, category);
CREATE INDEX IF NOT EXISTS idx_conv_user_time     ON conversations(user_id, created_at DESC);

-- 啟用 Row Level Security
ALTER TABLE memories      ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- ⚠️  移除舊的「開放給所有人」政策（若存在）
DROP POLICY IF EXISTS "allow_all_memories"      ON memories;
DROP POLICY IF EXISTS "allow_all_conversations" ON conversations;

-- 後端使用 service_role key 直接繞過 RLS，不需要任何 policy。
-- 不建立任何 anon policy → RLS 預設拒絕所有匿名請求。
-- 效果：持有 anon key 的外部呼叫者無法讀寫任何資料。

-- ============================================================
-- 若 memories 表已存在但缺少 user_id 欄位（升級用）
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memories' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE memories ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default';
        CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id, created_at DESC);
    END IF;
END $$;

-- ============================================================
-- 完成！接著到 Supabase → Storage 建立 bucket：
--   名稱：images
--   Public：✅ 開啟
-- ============================================================
