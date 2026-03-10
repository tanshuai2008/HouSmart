alter table users
add column if not exists onboarding_complete boolean not null default false;

update users u
set onboarding_complete = true
from user_onboarding_answers o
where o.user_id = u.id
  and o.primary_role_ques is not null
  and o.investment_experience_level_ques is not null
  and o.investment_goal_ques is not null
  and jsonb_typeof(o.priorities_ranking_ques) = 'array'
  and jsonb_array_length(o.priorities_ranking_ques) = 4;
