from uuid import UUID

from app.core.supabase_client import supabase


def _is_complete(payload: dict) -> bool:
    role = (payload.get("primary_role_ques") or "").strip()
    experience = (payload.get("investment_experience_level_ques") or "").strip()
    goal = (payload.get("investment_goal_ques") or "").strip()
    priorities = payload.get("priorities_ranking_ques") or []

    return bool(role and experience and goal and isinstance(priorities, list) and len(priorities) == 4)


def get_onboarding_answers_by_user_id(user_id: UUID) -> dict | None:
    response = (
        supabase
        .table("user_onboarding_answers")
        .select("*")
        .eq("user_id", str(user_id))
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def upsert_onboarding_answers(payload: dict) -> dict:
    response = (
        supabase
        .table("user_onboarding_answers")
        .upsert(payload, on_conflict="user_id")
        .execute()
    )

    supabase.table("users").update(
        {"onboarding_complete": _is_complete(payload)}
    ).eq("id", payload["user_id"]).execute()

    return response.data[0]
