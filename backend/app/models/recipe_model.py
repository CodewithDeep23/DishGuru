from pydantic import BaseModel, Field
from typing import List, Optional, Annotated
from datetime import datetime, timezone
from app.models.userModel import PyObjectId

# Sub Model
class Ingredient(BaseModel):
    name: str = Field(..., description="Name of the ingredient")
    quantity: Optional[str] = Field(..., description="Quantity of the ingredient, e.g., '2 cups'")
    

# Rating Model
class Rating(BaseModel):
    count: int = Field(0, description="Number of ratings")
    average: float = Field(0.0, description="Average rating score")
    user_ratings: Optional[dict[PyObjectId, float]] = {}

# Base Recipe Model
class RecipeBase(BaseModel):
    title: str
    ingredients: List[Ingredient]
    instructions: List[str]
    region: Optional[str] = None
    # cusine: Optional[str] = None
    dietary_preferences: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[Annotated[str, Field(pattern="^(Easy|Medium|Hard)$")]] = None
    tags: Optional[List[str]] = None
    nutritional_info: Optional[dict] = None
    ratings: Rating = Field(default_factory=Rating)
    owner: Optional[PyObjectId] = Field(None, description="User ID of the recipe owner")
    vector_embedding: Optional[List[float]] = Field(default=None, description="AI vector embedding for semantic search.")
    createdAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True

class RecipeInDB(RecipeBase):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    class Config:
        populate_by_name = True
        extra = "ignore"

class RecipePublic(RecipeBase):
    id: PyObjectId = Field(alias="_id")
    
    class Config:
        populate_by_name = True
        from_attributes = True