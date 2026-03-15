-- Latest Redfin city-level snapshot (one row per city/state)
--
-- Purpose:
-- - Fast lookup of the most recent median_price + sale_to_list_ratio per place.
-- - Complements `redfin_city_monthly_trends` which stores the last 36 months.
--
-- Run in Supabase SQL editor.

create table if not exists public.redfin_city_latest (
  city text not null,
  state text not null,
  period date not null,
  median_price bigint not null,
  sale_to_list_ratio double precision null,
  primary key (city, state)
);

create index if not exists redfin_city_latest_period_idx
  on public.redfin_city_latest (period);
