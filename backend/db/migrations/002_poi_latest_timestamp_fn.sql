-- Returns the latest POI cache timestamp for a given search radius.

create or replace function latest_poi_timestamp(
    lat double precision,
    lng double precision,
    radius_meters integer
) returns timestamptz
language sql
stable
as $$
    select max(p.created_at)
    from osm_poi_cache p
    where st_dwithin(
        p.location,
        st_setsrid(st_makepoint(lng, lat), 4326)::geography,
        radius_meters
    );
$$;
