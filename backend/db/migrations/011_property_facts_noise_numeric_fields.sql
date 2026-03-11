alter table if exists property_facts
    add column if not exists noise_index numeric(5,1),
    add column if not exists estimated_noise_db numeric(5,1);
