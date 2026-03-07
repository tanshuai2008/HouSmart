from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.core.firebase import create_firebase_user, verify_firebase_token
from app.services.auth_service import (
    get_user_by_email,
    get_user_by_firebase_uid,
    create_user,
    update_last_login,
)
from app.utils.password import hash_password, verify_password
from app.api.schemas.auth import RegisterRequest, LoginRequest


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register_user(payload: RegisterRequest):

    existing_user = get_user_by_email(payload.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    try:
        firebase_user = create_firebase_user(
            payload.email,
            payload.password,
        )

        hashed_password = hash_password(payload.password)

        user = create_user(
            firebase_uid=firebase_user.uid,
            email=payload.email,
            password=hashed_password,
            auth_provider="email",
        )

        return {
            "message": "User registered successfully",
            "user": user,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login_user(payload: LoginRequest):

    try:
        user = get_user_by_email(payload.email)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        hashed_password = user.get("password")
        auth_provider = user.get("auth_provider")

        if auth_provider != "email":
            raise HTTPException(
                status_code=400,
                detail="This account uses social login. Use /auth/google",
            )

        if not hashed_password or not verify_password(payload.password, hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        firebase_uid = user.get("firebase_uid")

        if firebase_uid:
            update_last_login(firebase_uid)

        return {
            "message": "Login successful",
            "user": user,
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/google")
def google_login(authorization: Optional[str] = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        decoded = verify_firebase_token(token)

        firebase_uid = decoded["uid"]
        email = decoded.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Google account missing email")

        user = get_user_by_firebase_uid(firebase_uid)

        if not user:
            user = create_user(
                firebase_uid=firebase_uid,
                email=email,
                password=None,
                auth_provider="google",
            )

        update_last_login(firebase_uid)

        return {
            "message": "Google login successful",
            "user": user,
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/verify")
def verify_user(authorization: Optional[str] = Header(None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        decoded = verify_firebase_token(token)

        firebase_uid = decoded["uid"]

        user = get_user_by_firebase_uid(firebase_uid)

        return {
            "valid": True,
            "user": user,
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
