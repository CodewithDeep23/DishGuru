import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRY", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRY", 7))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def create_token(data: Dict[str, any], secret_key: str, expires_delta: timedelta) -> str:
    """Generic function to create a JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(datetime.now(timezone.utc).timestamp())})
    return jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)

def create_access_token(subject: Any) -> str:
    """Creates a JWT access token containing the subject (e.g., user ID or email)."""
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # The 'sub' (subject) claim is standard for identifying the user
    return create_token({"sub": str(subject)}, ACCESS_TOKEN_SECRET, expires)

def create_refresh_token(subject: Any) -> str:
    """Creates a JWT refresh token."""
    expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token({"sub": str(subject)}, REFRESH_TOKEN_SECRET, expires)

def decode_token(token: str, secret_key: str) -> Dict | None:
    """Decodes a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            print("⚠️ Token has expired.")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        print("⚠️ Token expired (jwt.ExpiredSignatureError).")
        return None
    except jwt.InvalidTokenError:
        print("❌ Invalid token structure or signature.")
        return None