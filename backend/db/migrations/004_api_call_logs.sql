create table if not exists api_call_logs (
    id bigserial primary key,
    endpoint text not null,
    method text not null,
    status_code integer not null,
    request_json jsonb,
    response_json jsonb,
    user_id text,
    created_at timestamptz not null default now()
);

create index if not exists idx_api_call_logs_created_at on api_call_logs (created_at desc);
create index if not exists idx_api_call_logs_endpoint on api_call_logs (endpoint);
create index if not exists idx_api_call_logs_user_id on api_call_logs (user_id);
