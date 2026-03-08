CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION get_property_school_scores(search_address text)
RETURNS TABLE (
    school_name text,
    level text,
    housmart_school_score numeric,
    s_academic numeric,
    s_resource numeric,
    s_equity numeric
)
LANGUAGE sql
AS $$
SELECT
    sm.school_name,
    sm.level,
    sm.housmart_school_score,
    sm.s_academic,
    sm.s_resource,
    sm.s_equity
FROM properties p
JOIN property_school_district psd
ON p.id = psd.property_id
JOIN school_master sm
ON psd.district_id = sm.district_id
WHERE p.formatted_address % search_address
ORDER BY similarity(p.formatted_address, search_address) DESC
LIMIT 20;
$$;