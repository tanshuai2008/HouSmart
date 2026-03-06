-- Initial schema for active HouSmart backend endpoints.
-- Safe to run multiple times.

create extension if not exists postgis;

create table if not exists schema_migrations (
    version text primary key,
    applied_at timestamptz not null default now()
);

create table if not exists geo_tract_metrics (
    tract_geoid text primary key,
    state_fips text,
    county_fips text,
    median_income integer,
    education_bachelor_pct numeric(6,2),
    updated_at timestamptz not null default now()
);

create table if not exists flood_risk_cache (
    key text primary key,
    value jsonb not null,
    expires_at timestamptz not null,
    updated_at timestamptz not null default now()
);
create index if not exists idx_flood_risk_cache_expires_at on flood_risk_cache (expires_at);

create table if not exists flood_zones (
    lat double precision not null,
    lng double precision not null,
    fld_zone text,
    risk_label text not null,
    flood_score double precision not null,
    flood_data_unknown boolean not null default false,
    source text,
    updated_at timestamptz not null default now(),
    primary key (lat, lng)
);

create table if not exists transit_cache (
    key text primary key,
    value jsonb not null,
    expires_at timestamptz not null,
    updated_at timestamptz not null default now()
);
create index if not exists idx_transit_cache_expires_at on transit_cache (expires_at);

create table if not exists transit_scores (
    property_lat double precision not null,
    property_lng double precision not null,
    radius_meters integer not null,
    bus_stop_count integer not null,
    rail_station_count integer not null,
    nearest_stop_meters double precision,
    transit_score double precision not null,
    source text,
    updated_at timestamptz not null default now(),
    primary key (property_lat, property_lng)
);

create table if not exists noise_scores (
    id bigserial primary key,
    address text not null,
    latitude double precision not null,
    longitude double precision not null,
    distance_to_road double precision,
    noise_level text not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_noise_scores_address on noise_scores (address);

create table if not exists redfin_median_prices (
    id bigserial primary key,
    city text not null,
    state text not null,
    period date not null,
    median_price bigint not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_redfin_city_state_period
    on redfin_median_prices (city, state, period desc);

create table if not exists rent_estimate_cache (
    request_hash text primary key,
    address text,
    request_payload jsonb not null,
    response_payload jsonb not null,
    updated_at_epoch bigint not null
);

create table if not exists leaic_crosswalk (
    ori text primary key,
    agency_name text not null,
    agency_type text not null check (agency_type in ('city', 'county')),
    place_fips text,
    county_fips text,
    state_abbr text,
    updated_at timestamptz not null default now()
);
create index if not exists idx_leaic_place_type on leaic_crosswalk (place_fips, agency_type);
create index if not exists idx_leaic_county_type on leaic_crosswalk (county_fips, agency_type);

create table if not exists osm_poi_cache (
    id bigserial primary key,
    osm_key text not null,
    osm_value text not null,
    latitude double precision not null,
    longitude double precision not null,
    location geography(Point, 4326) not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_osm_poi_location on osm_poi_cache using gist (location);
create index if not exists idx_osm_poi_key_value on osm_poi_cache (osm_key, osm_value);

create or replace function count_pois(
    lat double precision,
    lng double precision,
    radius_meters integer,
    p_osm_key text,
    p_osm_values text[]
) returns integer
language sql
stable
as $$
    select count(*)::integer
    from osm_poi_cache p
    where p.osm_key = p_osm_key
      and p.osm_value = any(p_osm_values)
      and st_dwithin(
          p.location,
          st_setsrid(st_makepoint(lng, lat), 4326)::geography,
          radius_meters
      );
$$;
