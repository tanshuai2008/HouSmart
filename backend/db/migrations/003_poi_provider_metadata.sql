-- Adds POI provider metadata and helper function for latest provider lookup.

alter table if exists osm_poi_cache
    add column if not exists provider text;

update osm_poi_cache
set provider = 'google_places'
where provider is null;

alter table if exists osm_poi_cache
    alter column provider set default 'google_places';

alter table if exists osm_poi_cache
    alter column provider set not null;

create or replace function latest_poi_provider(
    lat double precision,
    lng double precision,
    radius_meters integer
) returns text
language sql
stable
as $$
    select p.provider
    from osm_poi_cache p
    where st_dwithin(
        p.location,
        st_setsrid(st_makepoint(lng, lat), 4326)::geography,
        radius_meters
    )
    order by p.created_at desc
    limit 1;
$$;
