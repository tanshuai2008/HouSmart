create table if not exists users (
    id bigserial primary key,
    firebase_uid text unique not null,
    email text unique not null,
    password text,
    auth_provider text not null check (auth_provider in ('email', 'google', 'apple', 'microsoft')),
    created_on timestamptz not null default now(),
    last_login timestamptz not null default now()
);

create index if not exists idx_users_email on users (email);
create index if not exists idx_users_firebase_uid on users (firebase_uid);
