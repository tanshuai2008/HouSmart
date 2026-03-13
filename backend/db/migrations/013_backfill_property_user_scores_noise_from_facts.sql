-- 012 was already applied in some environments before label-to-numeric mapping
-- was added. Backfill missing numeric noise scores from property_facts.noise_index.
update property_user_scores pus
set noise_score = pf.noise_index
from property_facts pf
where pus.run_id = pf.run_id
  and pus.property_id = pf.property_id
  and pus.noise_score is null
  and pf.noise_index is not null;
