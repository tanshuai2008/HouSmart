alter table if exists property_user_scores
    alter column noise_score type numeric(5,1)
    using case
        when noise_score is null then null
        when lower(btrim(noise_score)) = 'low' then 25.0
        when lower(btrim(noise_score)) = 'moderate' then 50.0
        when lower(btrim(noise_score)) = 'high' then 75.0
        when lower(btrim(noise_score)) = 'very high' then 90.0
        when btrim(noise_score) ~ '^-?[0-9]+(\.[0-9]+)?$' then (btrim(noise_score))::numeric(5,1)
        else null
    end;
