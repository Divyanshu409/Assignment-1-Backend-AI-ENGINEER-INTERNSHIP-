import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set (check .env)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter(prefix="/auth", tags=["auth"])

bearer_scheme = HTTPBearer(auto_error=False)


class AuthCredentials(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201, summary="Create a new user account")
def signup(payload: AuthCredentials):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="'email' and 'password' are required")

    try:
        result = supabase.auth.sign_up(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"user": result.user}


@router.post("/login", summary="Authenticate a user and return a JWT")
def login(payload: AuthCredentials):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="'email' and 'password' are required")

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "user": result.user,
    }


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Access token required")

    token = credentials.credentials
    try:
        result = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not result or not result.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return result.user


@router.post("/logout", status_code=204, summary="Terminate the user session")
def logout(user=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return None