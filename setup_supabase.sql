-- ============================================================
-- LINE Bot AI Agent — Supabase 資料庫初始化
-- 在 Supabase Dashboard → SQL Editor 執行此檔案
-- ============================================================

-- 長期記憶表
CREATE TABLE IF NOT EXISTS memories (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
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
CREATE INDEX IF NOT EXISTS idx_memories_created   ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_category  ON memories(category);
CREATE INDEX IF NOT EXISTS idx_conv_user_time     ON conversations(user_id, created_at DESC);

-- 啟用 Row Level Security（建議開啟）
ALTER TABLE memories      ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- 允許所有人完整存取（anon key 可讀寫）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'memories' AND policyname = 'allow_all_memories'
    ) THEN
        CREATE POLICY "allow_all_memories"
            ON memories FOR ALL USING (true) WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'conversations' AND policyname = 'allow_all_conversations'
    ) THEN
        CREATE POLICY "allow_all_conversations"
            ON conversations FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ============================================================
-- 完成！接著到 Supabase → Storage 建立 bucket：
--   名稱：images
--   Public：✅ 開啟
-- ============================================================
