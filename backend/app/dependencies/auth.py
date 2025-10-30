# app/dependencies/auth.py
from fastapi import Header, Depends, status, Request
from typing import Annotated, Dict, Optional
from app.utils.exception import ApiError
from app.utils.jwt import decode_token, ACCESS_TOKEN_SECRET
from app.database.connection import MongoDB
from app.models.userModel import UserPublic
from bson import ObjectId

# Utility to fetch user (should be in a repo layer for production)
async def get_user_by_id(user_id: str) -> Optional[UserPublic]:
    """Fetches a user by their ID from MongoDB and returns a UserPublic model."""
    db = MongoDB.get_db()
    try:
        if not ObjectId.is_valid(user_id):
            return None
        
        # We use '_id' here because the 'sub' in the JWT payload is the user's ObjectId string
        user_data = await db["users"].find_one({"_id": ObjectId(user_id)}, {
            "hashed_password": 0, # Exclude password
            "refreshToken": 0     # Exclude refresh token
        })
        
        if user_data:
            # Use UserPublic model to ensure only public data is returned and validated
            return UserPublic(**user_data)
    except Exception as e:
        print(f"Database error in get_user_by_id: {e}")
        return None
    return None

async def get_current_user(request: Request) -> UserPublic:
    """
    FastAPI dependency to verify JWT, fetch user, and inject the UserPublic model.
    Checks for token in Cookies (accessToken) first, then Authorization Header.
    """
    
    # 1. Check for token in Cookie
    token = request.cookies.get("accessToken")
    
    # 2. If not in cookie, check Authorization header
    if not token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.lower().startswith("bearer "):
            # Split the string to get the token part after "Bearer "
            token = authorization.split(" ", 1)[1]
    
    if not token:
        # 401 Unauthorized access
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Unauthorized access: Access token not provided.")

    # 3. Decode Token
    payload: Optional[Dict] = decode_token(token, ACCESS_TOKEN_SECRET)
    
    if payload is None:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token.")

    # 4. Extract user ID (subject claim) and Fetch User
    user_id = payload.get("sub")
    
    if not user_id:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid access token: No subject found.")
        
    user = await get_user_by_id(user_id) # Fetch from MongoDB
    
    if not user:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid access token: User not found.")
        
    # 5. Success: Return the user model
    return user

# Convenience alias for use in route handlers
AuthenticatedUser = Annotated[UserPublic, Depends(get_current_user)]