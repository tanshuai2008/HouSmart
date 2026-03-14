-- Add optional Redfin fields used by the dashboard graphs.
-- Run in Supabase SQL editor.

alter table if exists public.redfin_median_prices
  add column if not exists sale_to_list_ratio double precision;
