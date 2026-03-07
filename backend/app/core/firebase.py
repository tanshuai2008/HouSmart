import os
import firebase_admin
from firebase_admin import credentials, auth


def initialize_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    firebase_config = {
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    cred = credentials.Certificate(firebase_config)

    return firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str):
    initialize_firebase()
    decoded_token = auth.verify_id_token(id_token)
    return decoded_token


def create_firebase_user(email: str, password: str):
    initialize_firebase()

    user = auth.create_user(
        email=email,
        password=password,
    )

    return user