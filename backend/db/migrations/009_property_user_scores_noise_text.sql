alter table if exists property_user_scores
    alter column noise_score type varchar(80)
    using case when noise_score is null then null else noise_score::text end;
