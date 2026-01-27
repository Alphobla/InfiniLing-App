-- Vocabulary table
CREATE TABLE vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    word TEXT NOT NULL,
    lemma TEXT,
    translation TEXT,
    language_from TEXT NOT NULL,
    language_to TEXT NOT NULL,
    frequency_rank INTEGER,
    frequency_level TEXT,
    example_sentence_original TEXT,
    example_sentence_translation TEXT,
    primary_translation TEXT,
    secondary_translation TEXT,
    next_review_date DATE,
    review_interval_days INTEGER DEFAULT 1,
    easiness_factor FLOAT DEFAULT 2.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, lemma, language_from, language_to)
);

-- Index for fast user queries
CREATE INDEX idx_vocabulary_user_id ON vocabulary(user_id);
CREATE INDEX idx_vocabulary_language ON vocabulary(user_id, language_from);
CREATE INDEX idx_vocabulary_review ON vocabulary(user_id, next_review_date);

-- Vocabulary occurrence (review history)
CREATE TABLE vocabulary_occurrence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vocabulary_id UUID NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    review_date TIMESTAMPTZ DEFAULT NOW(),
    score INTEGER CHECK (score >= 0 AND score <= 5),
    easiness_factor FLOAT,
    interval_days INTEGER,
    repetitions INTEGER
);

CREATE INDEX idx_occurrence_vocabulary ON vocabulary_occurrence(vocabulary_id);

-- User settings
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    openai_api_key_encrypted TEXT,
    tokens_used_this_month INTEGER DEFAULT 0,
    token_limit INTEGER DEFAULT 100000,
    mother_tongue TEXT NOT NULL,
    last_language_pair TEXT,
    reset_date DATE DEFAULT (date_trunc('month', NOW()) + INTERVAL '1 month')::DATE,
    has_seen_intro BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security policies
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary_occurrence ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own vocabulary" ON vocabulary
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own vocabulary" ON vocabulary
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own vocabulary" ON vocabulary
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own vocabulary" ON vocabulary
    FOR DELETE USING (auth.uid() = user_id);

-- Same for occurrences (via vocabulary ownership)
CREATE POLICY "Users can view own occurrences" ON vocabulary_occurrence
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM vocabulary WHERE vocabulary.id = vocabulary_id AND vocabulary.user_id = auth.uid())
    );

CREATE POLICY "Users can insert own occurrences" ON vocabulary_occurrence
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM vocabulary WHERE vocabulary.id = vocabulary_id AND vocabulary.user_id = auth.uid())
    );

-- User settings
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);
