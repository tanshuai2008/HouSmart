alter table if exists user_properties
    add column if not exists state_fips varchar(2),
    add column if not exists county_fips varchar(5);

