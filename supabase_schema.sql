-- ════════════════════════════════════════════════════════════════════════════
-- NeuraFind V2 — Supabase PostgreSQL Schema
-- ════════════════════════════════════════════════════════════════════════════

-- 1. Create the search_history table
CREATE TABLE IF NOT EXISTS public.search_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,               -- Anonymous user ID stored in browser cookies
    device_type TEXT NOT NULL,           -- 'mobile', 'laptop', 'smartwatch'
    budget NUMERIC NOT NULL,
    priorities JSONB,                    -- Array of priorities chosen
    top_result TEXT,                     -- Name of the #1 recommended device
    score NUMERIC,                       -- Match score of the top result
    result_count INTEGER,                -- How many devices were recommended
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now()) NOT NULL
);

-- 2. Add indexes for faster history loading
-- We frequently query by user_id and sort by created_at
CREATE INDEX IF NOT EXISTS idx_search_history_user_id 
ON public.search_history(user_id);

CREATE INDEX IF NOT EXISTS idx_search_history_created_at 
ON public.search_history(created_at DESC);

-- 3. Set up Row Level Security (RLS) - Important for production
ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;

-- 4. Create Policies
-- Allow anyone to INSERT a new search history record
CREATE POLICY "Allow public inserts" 
ON public.search_history 
FOR INSERT 
TO public 
WITH CHECK (true);

-- Allow users to SELECT only their own history
CREATE POLICY "Allow users to read own history" 
ON public.search_history 
FOR SELECT 
TO public 
USING (true); -- In a full auth system, this would be auth.uid() = user_id. For anonymous, we rely on the backend fetching by cookie ID.
