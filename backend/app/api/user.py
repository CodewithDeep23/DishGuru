from fastapi import APIRouter, status, Depends
from app.database.connection import MongoDB
from app.dependencies.auth import AuthenticatedUser
from app.models.userModel import UserPublic, PyObjectId
from app.models.recipe_model import RecipePublic
from bson import ObjectId
from app.utils.exception import ApiError
from typing import List
from app.utils.pagination import get_pagination_params, PaginationParams

router = APIRouter(tags=["User"])

@router.get("/profile", response_model=UserPublic)
async def get_user_profile(
    current_user: AuthenticatedUser
):
    """
    Retrieves the profile of the currently authenticated user.
    FastAPI will automatically return status 200 and serialize the UserPublic object.
    """
    # The current_user object is already guaranteed to be a valid UserPublic model
    return current_user


# --- Favorites recipes endpoints
@router.post("/favorites/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite_recipe(
    current_user: AuthenticatedUser,
    recipe_id: str
):
    """
    Adds a recipe to the current user's favorites list.
    """
    db = MongoDB.get_db()
    users_collection = db["users"]
    if not ObjectId.is_valid(recipe_id):
        raise ApiError(400, "Invalid recipe ID format.")
    
    # Add to favorites if not already present
    result = await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$addToSet": {"favorites": ObjectId(recipe_id)}}   # Here we use $addToSet to avoid duplicates
    )
    
    if result.modified_count == 0:
        return {"message": "Recipe already in favorites or user not found."}
    return  # 204 No Content


# --- Remove from favorites
@router.delete("/favorites/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite_recipe(
    current_user: AuthenticatedUser,
    recipe_id: str
):
    """
    Removes a recipe from the current user's favorites list.
    """
    db = MongoDB.get_db()
    users_collection = db["users"]
    
    if not ObjectId.is_valid(recipe_id):
        raise ApiError(400, "Invalid recipe ID format.")
    
    result = await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$pull": {"favorites": ObjectId(recipe_id)}}   # $pull removes the item if it exists
    )
    
    if result.modified_count == 0:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Recipe not found in favorites.")
    return  # 204 No Content


# --- Fetch User's Recipes Endpoint ---
@router.get("/my_recipes", response_model=List[RecipePublic], status_code=status.HTTP_200_OK)
async def get_my_recipes(
    current_user: AuthenticatedUser,
    pagination: PaginationParams = Depends(get_pagination_params)
):
    """
    Retrieve all recipes created by the authenticated user.
    """
    recipe_db = MongoDB.get_db()["recipes"]
    print("Current User ID:", current_user.id)
    owner = recipe_db.find_one({"owner": ObjectId(current_user.id)})
    print("Recipe DB owner:", owner)
    try:
        cursor = recipe_db.find({"owner": ObjectId(current_user.id)}).skip(pagination.skip).limit(pagination.limit)
        
        my_recipes = await cursor.to_list(length=pagination.limit)
        return [RecipePublic.model_validate(recipe) for recipe in my_recipes]
    except Exception as e:
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to fetch user's recipes: {str(e)}")
  
  
# --- Fetch User's Favorite Recipes Endpoint ---
@router.get("/favorites", response_model=List[RecipePublic], status_code=status.HTTP_200_OK)
async def get_favorite_recipes(
    current_user: AuthenticatedUser,
    pagination: PaginationParams = Depends(get_pagination_params)
):
    """
    Retrieves the full recipe details for the user's favorite recipes.
    """
    user_db = MongoDB.get_db()["users"]
    recipe_db = MongoDB.get_db()["recipes"]
    try:
        user = await user_db.find_one({"_id": ObjectId(current_user.id)})
        
        if not user or not user.get("favorites"):
            return []  # Return empty list if no favorites
        
        favorites_ids = user["favorites"]
        
        cursor = recipe_db.find({"_id": {"$in": favorites_ids}}).skip(pagination.skip).limit(pagination.limit)
        
        favorite_recipes = await cursor.to_list(length=pagination.limit)
        return [RecipePublic.model_validate(recipe) for recipe in favorite_recipes]
    except Exception as e:
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to fetch favorite recipes: {str(e)}")