alter table if exists comparable_properties
    add column if not exists status varchar(50);

alter table if exists comparable_properties
    add column if not exists days_on_market integer;

update comparable_properties
set
    status = case
        when status is not null and lower(trim(status)) in ('active', 'for_rent', 'for rent') then 'active'
        when status is not null and trim(status) <> '' then 'inactive'
        when listed_date is not null and listed_date >= current_date - interval '30 days' then 'active'
        else 'inactive'
    end,
    days_on_market = case
        when days_on_market is not null and days_on_market >= 0 then days_on_market
        when listed_date is not null then greatest((current_date - listed_date), 0)
        else null
    end
where
    status is null
    or trim(status) = ''
    or lower(trim(status)) not in ('active', 'inactive')
    or days_on_market is null
    or days_on_market < 0;
