-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User profiles (linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT DEFAULT '',
    team_id UUID REFERENCES teams(team_id),
    role TEXT DEFAULT 'advisor' CHECK (role IN ('admin', 'advisor')),
    notification_prefs JSONB DEFAULT '{"email_t1": true, "email_t2": false, "push_t1": true}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_team ON profiles(team_id);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Add team_id to scored_leads for multi-tenancy
ALTER TABLE scored_leads ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(team_id);
CREATE INDEX IF NOT EXISTS idx_leads_team ON scored_leads(team_id);

-- RLS for profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile"
    ON profiles FOR SELECT
    TO authenticated
    USING (id = auth.uid());

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    TO authenticated
    USING (id = auth.uid());

-- Admins can read team profiles
CREATE POLICY "Admins can read team profiles"
    ON profiles FOR SELECT
    TO authenticated
    USING (
        team_id IN (
            SELECT p.team_id FROM profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );

-- RLS for teams
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Team members can read own team"
    ON teams FOR SELECT
    TO authenticated
    USING (
        team_id IN (
            SELECT p.team_id FROM profiles p WHERE p.id = auth.uid()
        )
    );

-- Update scored_leads RLS to be team-scoped
DROP POLICY IF EXISTS "Auth read leads" ON scored_leads;
CREATE POLICY "Team members can read their leads"
    ON scored_leads FOR SELECT
    TO authenticated
    USING (
        team_id IN (
            SELECT p.team_id FROM profiles p WHERE p.id = auth.uid()
        )
    );

-- Update events RLS — team members read events linked to their leads
DROP POLICY IF EXISTS "Auth read events" ON events;
CREATE POLICY "Team members can read linked events"
    ON events FOR SELECT
    TO authenticated
    USING (
        event_id IN (
            SELECT sl.event_id FROM scored_leads sl
            WHERE sl.team_id IN (
                SELECT p.team_id FROM profiles p WHERE p.id = auth.uid()
            )
        )
    );

-- Pipeline service role keeps full access via service_role key
-- The pipeline writes with service_role, web app reads with anon key + RLS
