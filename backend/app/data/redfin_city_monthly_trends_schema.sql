-- Thin Redfin city-level monthly trends table (for dashboard graphs)
--
-- Goal: keep storage small (e.g., ~36 months) by storing only the fields
-- the frontend graphs actually use.
--
-- Run in Supabase SQL editor.

create table if not exists public.redfin_city_monthly_trends (
  city text not null,
  state text not null,
  period date not null,
  median_price bigint not null,
  sale_to_list_ratio double precision null,
  primary key (city, state, period)
);

-- Optional: helps periodic cleanup (delete older than window)
create index if not exists redfin_city_monthly_trends_period_idx
  on public.redfin_city_monthly_trends (period);
