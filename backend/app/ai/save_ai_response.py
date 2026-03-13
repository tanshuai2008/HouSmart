create table public.property_ai_summaries (
  id                      uuid not null default gen_random_uuid(),
  run_id                  uuid not null,
  property_id             uuid not null,
  user_id                 uuid not null,

  verdict_color           varchar(10) not null,
  verdict_label           varchar(50) null,
  ai_confidence_pct       numeric(5,2) null,

  headline                text null,
  summary_blurb           text null,

  community_profile       text null,
  safety_and_amenities    text null,
  investment_suitability  text null,
  verdict_explanation     text null,

  key_strengths           jsonb null,
  key_risks               jsonb null,

  data_completeness_pct   numeric(5,1) null,
  missing_data_note       text null,
  admin_review_required   boolean not null default false,
  validation_errors       jsonb null,
  validation_warnings     jsonb null,

  model_used              varchar(100) null,
  policy_injected         boolean not null default false,
  policy_state            varchar(10) null,

  created_at              timestamptz not null default now(),

  constraint property_ai_summaries_pkey primary key (id),
  constraint property_ai_summaries_run_id_fkey
    foreign key (run_id) references property_analysis_runs(run_id) on delete cascade,
  constraint property_ai_summaries_run_id_key unique (run_id)
);

create index idx_ai_summaries_property_user
  on public.property_ai_summaries(property_id, user_id);