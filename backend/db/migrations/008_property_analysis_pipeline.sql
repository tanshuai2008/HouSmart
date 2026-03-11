create extension if not exists pgcrypto;

create table if not exists user_properties (
    property_id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id) on delete cascade,
    address text not null,
    normalized_address text,
    latitude double precision,
    longitude double precision,
    rent numeric(12,2),
    rent_currency varchar(10) default 'USD',
    property_type varchar(50),
    state_fips varchar(2),
    county_fips varchar(5),
    bedrooms integer,
    bathrooms numeric(4,1),
    square_footage integer,
    year_built integer,
    last_sale_date date,
    last_sale_price numeric(14,2),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists uq_user_properties_user_address
on user_properties(user_id, lower(address));

create index if not exists idx_user_properties_user_id
on user_properties(user_id);

create table if not exists property_analysis_runs (
    run_id uuid primary key default gen_random_uuid(),
    property_id uuid not null references user_properties(property_id) on delete cascade,
    status varchar(20) not null default 'completed',
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    error_message text,
    created_at timestamptz not null default now()
);

create index if not exists idx_runs_property_created
on property_analysis_runs(property_id, created_at desc);

create unique index if not exists uq_runs_run_property
on property_analysis_runs(run_id, property_id);

create table if not exists property_facts (
    fact_id bigserial primary key,
    property_id uuid not null references user_properties(property_id) on delete cascade,
    run_id uuid not null unique,
    median_property_price numeric(14,2),
    median_income numeric(14,2),
    median_income_currency varchar(10) default 'USD',
    bachelor_percentage numeric(5,2),
    rent_to_price numeric(8,3),
    affordability_index numeric(8,3),
    tenant_quality_index varchar(80),
    local_crime_index numeric(10,4),
    national_crime_index numeric(10,4),
    flood_zone varchar(50),
    flood_risk_label varchar(80),
    transit_radius_meters integer,
    nearest_stop_distance numeric(10,2),
    bus_stop_count integer,
    rail_station_count integer,
    distance_to_road numeric(10,2),
    total_schools integer,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint fk_property_facts_run_property
        foreign key (run_id, property_id)
        references property_analysis_runs(run_id, property_id)
        on delete cascade
);

create index if not exists idx_property_facts_property_created
on property_facts(property_id, created_at desc);

create table if not exists comparable_properties (
    comparable_id uuid primary key default gen_random_uuid(),
    property_id uuid not null references user_properties(property_id) on delete cascade,
    run_id uuid not null references property_analysis_runs(run_id) on delete cascade,
    address text,
    property_type varchar(50),
    bedrooms integer,
    bathrooms numeric(4,1),
    square_footage integer,
    year_built integer,
    status varchar(50),
    rental_price numeric(12,2),
    listed_type varchar(50),
    listed_date date,
    distance numeric(10,3),
    correlation_score numeric(6,3),
    created_at timestamptz not null default now()
);

create index if not exists idx_comparables_property_run
on comparable_properties(property_id, run_id);

create table if not exists property_user_scores (
    id bigserial primary key,
    user_id uuid not null references users(id) on delete cascade,
    property_id uuid not null references user_properties(property_id) on delete cascade,
    run_id uuid not null,
    amenity_score numeric(6,2),
    transit_score numeric(6,2),
    noise_score varchar(80),
    school_score numeric(6,2),
    safety_score numeric(6,2),
    flood_score numeric(6,2),
    scoring_version varchar(30),
    calculated_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint fk_property_user_scores_run_property
        foreign key (run_id, property_id)
        references property_analysis_runs(run_id, property_id)
        on delete cascade
);

create unique index if not exists uq_property_user_scores_scope
on property_user_scores(user_id, property_id, run_id);

create index if not exists idx_property_user_scores_user_property
on property_user_scores(user_id, property_id, calculated_at desc);
