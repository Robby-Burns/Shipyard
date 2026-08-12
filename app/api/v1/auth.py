import time
import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.config.settings import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Development Authentication"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

from typing import Literal

@router.post("/token", response_model=TokenResponse)
async def generate_dev_token(username: str = "dev_user", role: Literal["admin", "developer", "viewer"] = "admin"):
    """
    DEVELOPMENT ONLY: Instantly generate a signed JWT token for sandbox testing.
    This route will return a HTTP 403 Forbidden error in production environments.
    """
    if settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development token generation is disabled in production environments."
        )

    payload = {
        "sub": username,
        "email": f"{username}@shipyard.local",
        "role": role,
        "exp": int(time.time()) + (settings.access_token_expire_minutes * 60)
    }
    
    token = jwt.encode(
        payload, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return TokenResponse(access_token=token, token_type="bearer")
