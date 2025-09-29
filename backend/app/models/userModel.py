from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from typing import List, Optional, Annotated
from datetime import datetime, timezone
from bson import ObjectId
# from app.utils.helper import PyObjectId

PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if isinstance(v, ObjectId) else v)]

class UserInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: EmailStr
    fullName: str
    region: str
    favorites: Optional[List[PyObjectId]] = []
    hashed_password: str = Field(..., alias="password")
    
    refreshToken: Optional[str] = None
    createdAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True
        extra = "ignore"

# Model for user regestration
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    fullName: str
    region: str
    password: str  # Plain password for registration


# Model for public user data (output) - NEVER include password or tokens
class UserPublic(BaseModel):
    id: PyObjectId = Field(alias="_id")
    username: str
    email: EmailStr
    fullName: str
    region: str
    favorites: Optional[List[PyObjectId]] = []
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
    
    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True
        
        
# --- NEW RESPONSE MODEL FOR LOGIN/TOKEN FLOW ---
class TokenResponse(BaseModel):
    """Standardized response model for login/token issue."""
    success: bool = True
    message: str = "Login successful"
    user: UserPublic
    access_token: str
    token_type: str = "Bearer"