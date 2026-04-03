-- Money in Motion — Supabase table setup with RLS

-- Events table
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    person_name TEXT DEFAULT '',
    company_name TEXT DEFAULT '',
    filed_at TIMESTAMPTZ,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    url TEXT DEFAULT '',
    raw_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_events_source ON events(event_type, source_id);
CREATE INDEX IF NOT EXISTS idx_events_detected ON events(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_company ON events(company_name);

-- Scored leads table
CREATE TABLE IF NOT EXISTS scored_leads (
    lead_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(event_id),
    score INTEGER NOT NULL DEFAULT 0,
    tier TEXT NOT NULL DEFAULT 'T3',
    situation_brief TEXT DEFAULT '',
    talking_points JSONB DEFAULT '[]',
    outreach_status TEXT DEFAULT 'pending',
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_tier ON scored_leads(tier);
CREATE INDEX IF NOT EXISTS idx_leads_score ON scored_leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_outreach ON scored_leads(outreach_status);
CREATE INDEX IF NOT EXISTS idx_leads_event ON scored_leads(event_id);

-- Pipeline runs table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running',
    events_detected INTEGER DEFAULT 0,
    events_new INTEGER DEFAULT 0,
    t1_count INTEGER DEFAULT 0,
    t2_count INTEGER DEFAULT 0,
    t3_count INTEGER DEFAULT 0,
    alerts_sent INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    scoring_failures INTEGER DEFAULT 0,
    api_cost_estimate FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_started ON pipeline_runs(started_at DESC);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER events_updated_at
    BEFORE UPDATE ON events FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER leads_updated_at
    BEFORE UPDATE ON scored_leads FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER runs_updated_at
    BEFORE UPDATE ON pipeline_runs FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Row Level Security
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE scored_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Auth read events" ON events FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth insert events" ON events FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Auth read leads" ON scored_leads FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth insert leads" ON scored_leads FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Auth update leads" ON scored_leads FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Auth read runs" ON pipeline_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Auth manage runs" ON pipeline_runs FOR ALL TO authenticated USING (true);
