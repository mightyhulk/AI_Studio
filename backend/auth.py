import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import bcrypt
import jwt

router = APIRouter(prefix="/auth", tags=["auth"])

# Use an environment variable or dummy for Client ID
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID" # Place holder
JWT_SECRET = "super_secret_alexandria_key_123"
JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Dummy DB
# Format: {"email": {"name": "...", "hashed_password": "...", "plan": "Premium"}}
FAKE_DB = {
    "scholar@alexandria.ai": {
        "name": "Eleanor Scholar",
        "hashed_password": hash_password("password123"),
        "plan": "Premium"
    }
}

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    token: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

def create_jwt(email: str, name: str, plan: str):
    payload = {
        "sub": email,
        "name": name,
        "plan": plan,
        "exp": time.time() + 3600 * 24 # 1 day expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/login")
def login(req: LoginRequest):
    user = FAKE_DB.get(req.email.lower())
    
    # Check if account exists at all
    if not user:
        raise HTTPException(status_code=404, detail="Account not found. Please create an account first.")
        
    # Check if they try to use a password on a Google-only account
    if not user["hashed_password"]:
        raise HTTPException(status_code=400, detail="This account was created via Google. Please use Google Sign-In.")
        
    # Check correct password
    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password.")
    
    token = create_jwt(req.email.lower(), user["name"], user["plan"])
    return {"token": token, "user": {"name": user["name"], "email": req.email.lower(), "plan": user["plan"]}}

@router.post("/signup")
def signup(req: SignupRequest):
    email = req.email.lower()
    if email in FAKE_DB:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    FAKE_DB[email] = {
        "name": req.name,
        "hashed_password": hash_password(req.password),
        "plan": "Premium"
    }
    token = create_jwt(email, req.name, "Premium")
    return {"token": token, "user": {"name": req.name, "email": email, "plan": "Premium"}}

import httpx

@router.post("/google")
async def google_login(req: GoogleLoginRequest):
    try:
        # Verify the access token by fetching user info
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {req.token}"}
            )
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch Google user info: {response.text}")
            
        user_info = response.json()
        email = user_info.get("email")
        if not email:
            raise ValueError("Email not found in Google profile")
            
        name = user_info.get("name", "Google User")

        # Create or update user
        if email not in FAKE_DB:
            FAKE_DB[email] = {
                "name": name,
                "hashed_password": "", # No password for Google auth
                "plan": "Premium"
            }
        
        token = create_jwt(email, FAKE_DB[email]["name"], FAKE_DB[email]["plan"])
        return {"token": token, "user": {"name": FAKE_DB[email]["name"], "email": email, "plan": FAKE_DB[email]["plan"]}}

    except Exception as e:
        # Invalid token
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
