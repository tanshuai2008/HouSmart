create table if not exists user_onboarding_answers (
    id bigserial primary key,
    user_id uuid not null unique references users(id) on delete cascade,
    primary_role_ques text,
    investment_experience_level_ques text,
    investment_goal_ques text,
    priorities_ranking_ques jsonb not null default '[]'::jsonb,
    created_on timestamptz not null default now(),
    updated_on timestamptz not null default now()
);

create index if not exists idx_user_onboarding_answers_user_id on user_onboarding_answers (user_id);

create or replace function set_user_onboarding_answers_updated_on()
returns trigger as $$
begin
    new.updated_on = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_user_onboarding_answers_updated_on on user_onboarding_answers;

create trigger trg_user_onboarding_answers_updated_on
before update on user_onboarding_answers
for each row
execute function set_user_onboarding_answers_updated_on();
