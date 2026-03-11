CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE FUNCTION get_property_school_scores(search_address text)
RETURNS TABLE (
    school_name text,
    level text,
    housmart_school_score numeric,
    s_academic numeric,
    s_resource numeric,
    s_equity numeric,
    academic_percentile numeric,
    growth_percentile numeric,
    math_percentile numeric,
    score_fields_used text,
    score_fields_missing text
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  -- We use a CTE (a temporary result) to find the single closest matching property first
  WITH closest_property AS (
      SELECT p.id 
      FROM properties p
      -- It must be at least somewhat similar to avoid random matches
      WHERE similarity(p.formatted_address, search_address) > 0.2 
      -- Order by the most similar match at the very top
      ORDER BY similarity(p.formatted_address, search_address) DESC
      LIMIT 1
  )
  -- Now we join that single closest property to the school data
  SELECT 
    sm.school_name, 
    sm.level, 
    sm.housmart_school_score, 
    sm.s_academic, 
    sm.s_resource, 
    sm.s_equity,
    sm.academic_percentile,
    sm.growth_percentile,
    sm.math_percentile,
    sm.score_fields_used,
    sm.score_fields_missing
  FROM closest_property cp
  JOIN property_school_district psd ON cp.id = psd.property_id
  JOIN school_master sm ON psd.district_id = sm.district_id
  ORDER BY sm.housmart_school_score DESC NULLS LAST;
END;
$$;