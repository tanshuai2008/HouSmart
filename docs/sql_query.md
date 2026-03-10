## Rent Estimation Table


create table if not exists rent_estimate_cache (
    request_hash text primary key,
    address text not null,
    request_payload jsonb not null,
    response_payload jsonb not null,
    updated_at_epoch bigint not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_rent_estimate_cache_updated
    on rent_estimate_cache (updated_at_epoch);

## Crime Safety Crosswalk Table

create table if not exists leaic_crosswalk (
    ori text primary key,
    agency_name text not null,
    agency_type text not null check (agency_type in ('city', 'county')),
    place_fips text,
    county_fips text,
    state_abbr text,
    created_at timestamptz not null default now()
);

create index if not exists idx_leaic_crosswalk_place
    on leaic_crosswalk (place_fips) where place_fips is not null;

create index if not exists idx_leaic_crosswalk_county
    on leaic_crosswalk (county_fips) where county_fips is not null;

## Crime Score Cache Table

create table if not exists crime_score_cache (
    request_hash text primary key,
    address text not null,
    ori text not null,
    data_year integer not null,
    response_payload jsonb not null,
    updated_at_epoch bigint not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_crime_score_cache_ori_year
    on crime_score_cache (ori, data_year);

create index if not exists idx_crime_score_cache_updated
    on crime_score_cache (updated_at_epoch);


# Crime National Benchmark

create table if not exists crime_national_benchmark (
    benchmark_key text primary key,
    payload jsonb not null,
    updated_at_epoch bigint not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_crime_national_benchmark_updated
    on crime_national_benchmark (updated_at_epoch);
