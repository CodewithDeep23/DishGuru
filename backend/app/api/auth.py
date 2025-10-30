# app/api/v1/auth.py
from fastapi import APIRouter, status, Response, Request
from app.models.userModel import UserCreate, UserPublic, TokenResponse
from app.utils.hashPass import hash_password, is_password_correct
from app.utils.exception import ApiError
from app.database.connection import get_db
from app.utils.jwt import create_access_token, create_refresh_token, decode_token, REFRESH_TOKEN_SECRET
from datetime import datetime, timezone
from app.dependencies.auth import AuthenticatedUser
from typing import Dict, Optional
from bson import ObjectId

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    db = get_db()
    users_collection = db["users"]
    
    # Check uniqueness
    if await users_collection.find_one({"email": user_data.email}):
        raise ApiError(status.HTTP_409_CONFLICT, "User with this email already exists.")
    if await users_collection.find_one({"username": user_data.username}):
        raise ApiError(status.HTTP_409_CONFLICT, "Username is already taken.")

    # Prepare data
    hashed_password = hash_password(user_data.password)
    user_doc = user_data.model_dump(exclude={"password"})
    
    # --- FIX: Manually set the timestamps before insertion ---
    now = datetime.now(timezone.utc)
    user_doc["hashed_password"] = hashed_password
    user_doc["createdAt"] = now
    user_doc["updatedAt"] = now
    
    # Insert and retrieve
    result = await users_collection.insert_one(user_doc)
    
    # Retrieve the document to ensure all fields (like defaults) are returned
    created_user_doc = await users_collection.find_one(
        {"_id": result.inserted_id},
        {"hashed_password": 0, "refreshToken": 0} 
    )
    
    if not created_user_doc:
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, "Registration succeeded but user retrieval failed.")
        
    # FastAPI automatically handles the status code and uses the response_model
    return UserPublic(**created_user_doc)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    email: str, 
    password: str, 
    response: Response # Used to set HttpOnly cookies
):
    db = get_db()
    users_collection = db["users"]
    
    # 1. Find user (select password to verify)
    user_doc = await users_collection.find_one({"email": email})
    if not user_doc:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")
        
    # 2. Verify password
    hashed_password = user_doc.get("hashed_password") 
    if not is_password_correct(password, hashed_password):
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")
        
    user_id = str(user_doc["_id"])
    
    # 3. Generate tokens
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)
    
    # 4. Save refresh token (for revocation/renewal)
    now = datetime.now(timezone.utc)
    await users_collection.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"refreshToken": refresh_token, "updatedAt": now}}
    )
    
    # 5. Set HttpOnly cookies (Best Practice for browser clients)
    cookie_params = {
        "httponly": True,
        "secure": True, # REQUIRE HTTPS in production
        "samesite": "Lax",
        "max_age": 7 * 24 * 60 * 60
    }
    
    response.set_cookie(key="accessToken", value=access_token, **cookie_params)
    response.set_cookie(key="refreshToken", value=refresh_token, **cookie_params)
    
    # 6. Retrieve UserPublic model for response
    user_public = await users_collection.find_one(
        {"_id": user_doc["_id"]},
        {"hashed_password": 0, "refreshToken": 0}
    )

    # 7. Return the standardized TokenResponse
    return TokenResponse(
        user=UserPublic(**user_public),
        access_token=access_token,
        message="Login successful"
    )
    

# --- NEW ENDPOINT FOR LOGOUT ---
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    current_user: AuthenticatedUser,
    response: Response
):
    """
    Logs out the user by clearing the authentication cookies.
    """
    db = get_db()
    users_collection = db["users"]
    
    # 2. Revoke Refresh Token (Essential Security Step)
    # This prevents the old refresh token from being used to get a new access token
    try:
        await users_collection.update_one(
            {"_id": current_user.id}, # Use the authenticated user's ID
            {"$set": {"refreshToken": None}}
        )
    except Exception as e:
        # Log the error but continue, as cookie deletion is the priority
        print(f"Error revoking refresh token for user {current_user.id}: {e}")
    
    # Clear the cookies by setting them to empty and expiring them immediately
    response.delete_cookie(
        key="accessToken",
        httponly=True,
        secure=True, 
        samesite="Lax"
    )
    response.delete_cookie(
        key="refreshToken",
        httponly=True,
        secure=True, 
        samesite="Lax"
    )
    
    return {
        "success": True,
        "message": "Logged out successfully."
    }


@router.post("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_token(request: Request, response: Response):
    """
    Endpoint to refresh the access token using a valid refresh token.
    """

    incomingRefreshToken = request.cookies.get("refreshToken")

    # If not in cookie, check Authorization header
    if not incomingRefreshToken:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.lower().startswith("bearer "):
            # Split the string to get the token part after "Bearer "
            incomingRefreshToken = authorization.split(" ", 1)[1]

    if not incomingRefreshToken:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Refresh token not provided.")
    
    # 1. Decode and validate the refresh token
    payload: Optional[Dict] = decode_token(incomingRefreshToken, REFRESH_TOKEN_SECRET)

    if payload is None:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.")
    
    user_id = payload.get("sub")
    if not user_id:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token: No subject found.")
    
    db = get_db()
    user = await db["users"].find_one({"_id": ObjectId(user_id)})

    if not user or user.get("refreshToken") != incomingRefreshToken:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "Refresh token is not recognized.")
    
    # 3. Generate tokens
    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)

    # 4. Save refresh token (for revocation/renewal)
    now = datetime.now(timezone.utc)
    await db['users'].update_one(
        {"_id": user["_id"]},
        {"$set": {"refreshToken": refresh_token, "updatedAt": now}}
    )
    
    # 5. Set HttpOnly cookies (Best Practice for browser clients)
    cookie_params = {
        "httponly": True,
        "secure": True, # REQUIRE HTTPS in production
        "samesite": "Lax",
        "max_age": 7 * 24 * 60 * 60
    }
    
    response.set_cookie(key="accessToken", value=access_token, **cookie_params)
    response.set_cookie(key="refreshToken", value=refresh_token, **cookie_params)

    return {
        "status": "success",
        "message": "Access token refreshed successfully.",
    }