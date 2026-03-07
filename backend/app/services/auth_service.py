from datetime import datetime
from typing import Optional

from app.core.supabase_client import supabase


def get_user_by_email(email: str) -> Optional[dict]:
    response = (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def get_user_by_firebase_uid(firebase_uid: str) -> Optional[dict]:
    response = (
        supabase
        .table("users")
        .select("*")
        .eq("firebase_uid", firebase_uid)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def create_user(
    firebase_uid: str,
    email: str,
    password: Optional[str],
    auth_provider: str,
) -> dict:

    payload = {
        "firebase_uid": firebase_uid,
        "email": email,
        "password": password,
        "auth_provider": auth_provider,
        "created_on": datetime.utcnow().isoformat(),
        "last_login": datetime.utcnow().isoformat(),
    }

    response = (
        supabase
        .table("users")
        .insert(payload)
        .execute()
    )

    return response.data[0]


def update_last_login(firebase_uid: str):

    (
        supabase
        .table("users")
        .update({
            "last_login": datetime.utcnow().isoformat()
        })
        .eq("firebase_uid", firebase_uid)
        .execute()
    )