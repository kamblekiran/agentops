import pyrebase
import os
from dotenv import load_dotenv

load_dotenv()

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "databaseURL": "https://dummy.firebaseio.com",  # Optional but required by Pyrebase
    "storageBucket": "dummy.appspot.com"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

def login_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return {
            "email": email,
            "idToken": user['idToken'],
            "refreshToken": user['refreshToken'],
            "localId": user.get("localId", ""),
            "expiresIn": user.get("expiresIn", "3600")
        }
    except Exception as e:
        print("Login error:", e)
        return None

def verify_id_token(token):
    try:
        # Only works if the token is still valid
        user_info = auth.get_account_info(token)
        if user_info and "users" in user_info:
            return user_info
        else:
            print("Token structure unexpected:", user_info)
            return None
    except Exception as e:
        print("Token verification failed:", e)
        return None

def refresh_id_token(refresh_token):
    try:
        refreshed_user = auth.refresh(refresh_token)
        return {
            "idToken": refreshed_user.get("idToken"),
            "refreshToken": refreshed_user.get("refreshToken"),
            "localId": refreshed_user.get("userId")
        }
    except Exception as e:
        print("Token refresh error:", e)
        return None
