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
