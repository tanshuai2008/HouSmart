-- Supabase cache tables used by services for read-through caching.
-- Run these in Supabase SQL editor (or via migrations) once per project.

-- Median house price cache (key/value with TTL)
create table if not exists public.median_house_price_cache (
  key text primary key,
  value jsonb not null,
  expires_at timestamptz not null
);

create index if not exists median_house_price_cache_expires_at_idx
  on public.median_house_price_cache (expires_at);

-- Noise estimate cache (key/value with TTL)
create table if not exists public.noise_cache (
  key text primary key,
  value jsonb not null,
  expires_at timestamptz not null
);

create index if not exists noise_cache_expires_at_idx
  on public.noise_cache (expires_at);
