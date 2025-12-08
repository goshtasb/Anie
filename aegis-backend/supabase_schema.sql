-- Aegis Supabase Schema
-- Run this in your Supabase Dashboard -> SQL Editor

-- 1. GUESTS TABLE (For MVP Guest Mode)
-- Tracks device-based credits without requiring authentication
create table if not exists public.guests (
  id uuid default uuid_generate_v4() primary key,
  device_id text unique not null,
  credits integer default 5,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. SCAN CACHE TABLE (Cost Saver)
-- Stores analysis results to avoid re-analyzing the same URL
create table if not exists public.scan_cache (
  id uuid default uuid_generate_v4() primary key,
  url_hash text unique not null,
  url text not null,
  ani_score integer,
  scan_data jsonb not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. ENABLE ROW LEVEL SECURITY
alter table public.guests enable row level security;
alter table public.scan_cache enable row level security;

-- 4. RLS POLICIES
-- Allow service role (backend) full access
-- Guests table: Backend can read/write all
create policy "Service role full access to guests"
  on public.guests
  for all
  using (true)
  with check (true);

-- Cache table: Backend can read/write all
create policy "Service role full access to cache"
  on public.scan_cache
  for all
  using (true)
  with check (true);

-- 5. INDEXES for performance
create index if not exists idx_guests_device_id on public.guests(device_id);
create index if not exists idx_scan_cache_url_hash on public.scan_cache(url_hash);
create index if not exists idx_scan_cache_ani_score on public.scan_cache(ani_score);

-- 6. SCAN EVENTS TABLE (V4.0 Data Exhaust / Firehose)
-- Captures EVERY interaction for analytics/B2B data
create table if not exists public.scan_events (
  id uuid default uuid_generate_v4() primary key,
  user_id text default 'anonymous',
  url text not null,
  url_hash text,                    -- V4.1: B2B aggregation key (Nuclear Hash)
  ani_score integer,
  action_type text,                 -- 'NEW_SCAN' or 'CACHE_HIT'
  origin_location text,             -- Geopolitical origin
  geo_country text,                 -- User's country (from Cloudflare headers)
  device_type text,                 -- 'mobile', 'extension', 'web'
  meta jsonb,                       -- User agent, etc.
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,

  -- V4.4 Silent Feedback columns
  user_feedback text,               -- 'UP' or 'DOWN'
  correction_note text,             -- Optional reason for feedback
  feedback_timestamp timestamp with time zone
);

alter table public.scan_events enable row level security;

create policy "Service role full access to scan_events"
  on public.scan_events
  for all
  using (true)
  with check (true);

create index if not exists idx_scan_events_url_hash on public.scan_events(url_hash);
create index if not exists idx_scan_events_created_at on public.scan_events(created_at);
create index if not exists idx_scan_events_user_feedback on public.scan_events(user_feedback);

-- 6. (OPTIONAL) PROFILES TABLE for future Auth integration
-- Uncomment when moving to Option B (Real Auth)
/*
create table if not exists public.profiles (
  id uuid references auth.users not null primary key,
  email text,
  credits integer default 5,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.profiles enable row level security;

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, credits)
  values (new.id, new.email, 5);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
*/
