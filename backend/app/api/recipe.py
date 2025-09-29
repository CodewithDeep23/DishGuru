from fastapi import APIRouter, status, Depends
from typing import List, Dict, Optional
from app.dependencies.auth import AuthenticatedUser
from app.database.connection import get_db
from app.models.userModel import UserPublic, PyObjectId
from app.models.recipe_model import RecipePublic, RecipeInDB, Ingredient, RecipeBase
from app.utils.exception import ApiError
from datetime import datetime, timezone
from bson import ObjectId
import json

# --- NEW: Import the embedding service ---
from app.services.embedding_service import get_embedding
from app.models.request_model import VectorSearchRequest, RatingRequest
from app.utils.pagination import get_pagination_params, PaginationParams

router = APIRouter(tags=["Recipes"])

# --- Recipe Generation Endpoint ---
@router.post("/generate", response_model=List[RecipePublic], status_code=status.HTTP_201_CREATED)
async def generate_recipes(
    current_user: AuthenticatedUser,
    ingredients: List[Ingredient],
    region: Optional[str] = None,
    dietary_preferences: Optional[str] = None
):
    """
    Generate recipes using LLM based on scanned ingredients and user context.
    """
    recipe_db = get_db()["recipes"]
    # print("Ingredients", ingredients)
    ingredients_str = ", ".join([i.name for i in ingredients])
    # print(ingredients_str)
    
    # print("Region: ", region)
    
    # If region is None
    if not region or region.strip() == "":
        region = current_user.region
        
    # print("region after: ", region)
    
    try:
        ingredients_str = ", ".join([i.name for i in ingredients])
        
        dietary_pref = dietary_preferences if dietary_preferences else "None"
        
        # Prompt construction
        prompt = f"""
        You are an expert culinary AI assistant. Your task is to generate practical and appealing recipe suggestions based on a list of ingredients provided by a user.

        ### CONTEXT
        - User's primary region: "{region}"
        - Detected ingredients: "{ingredients_str}"
        - User's dietary preferences: "{dietary_pref}"

        ### TASK
        Generate 2 distinct recipe suggestions that prominently feature the detected ingredients.
        1.  Recipe 1 (Regional Focus): Create a recipe that is popular in or inspired by the user's region.
        2.  Recipe 2 (Creative/Alternative): Create a creative or widely-known recipe that is a great way to use the ingredients, even if it's not specific to the user's region.

        ### RULES
        - You may add up to 3 common pantry staples (e.g., oil, salt, pepper, water, common spices like turmeric or chili powder) if they are essential for the recipe. List them in the ingredients.
        - Prioritize using the detected ingredients.
        - The instructions should be a clear, numbered list of steps.

        ### OUTPUT FORMAT
        Your entire response MUST be a single, valid JSON object. Do not include any text or explanations outside of the JSON. The structure must follow this exact schema:

        Return valid JSON:
        {{
          "recipe_suggestions": [
            {{
              "title": "...",
              "ingredients": [
                                {{"name": "...", "quantity": "..."}},
	                            {{"name": "...", "quantity": "..."}}
                             ],
              "instructions": ["Step 1...", "Step 2..."],
              "region": "{region}",
              "dietary_preferences": "{dietary_pref}",
              "prep_time_minutes": int,
              "cook_time_minutes": int,
              "servings": int,
              "difficulty": "Easy/Hard/Medium",
              "tags": ["tag1", "tag2"],
              "nutritional_info": {{}}
            }}
          ]
        }}
        """
        
        # TODO: LLM response (OpenAI or other)
        
        
        # Suppose this is my response from LLM
        response = {
            "recipe_suggestions": [
                {
                    "title": "Aloo Palak Masala with Capsicum",
                    "ingredients": [
                        {"name": "Paalak (Spinach)", "quantity": "200g, chopped"},
                        {"name": "Potato", "quantity": "2 medium, diced"},
                        {"name": "Capsicum", "quantity": "1 medium, chopped"},
                        {"name": "Tomato", "quantity": "2 medium, pureed"},
                        {"name": "Oil", "quantity": "2 tbsp"},
                        {"name": "Salt", "quantity": "to taste"},
                        {"name": "Turmeric powder", "quantity": "1/2 tsp"},
                        {"name": "Red chili powder", "quantity": "1/2 tsp"},
                    ],
                    "instructions": [
                        "1. Heat oil in a pan and add diced potatoes. Fry lightly until golden.",
                        "2. Add chopped capsicum and sauté for 2 minutes.",
                        "3. Stir in the tomato puree, turmeric, red chili powder, and salt. Cook until oil separates.",
                        "4. Add chopped spinach and mix well. Cover and cook on low heat until spinach is soft and potatoes are cooked.",
                        "5. Serve hot with roti or rice.",
                    ],
                    "region": "Delhi/North Indian",
                    "dietary_preferences": "Vegetarian",
                    "prep_time_minutes": 15,
                    "cook_time_minutes": 25,
                    "servings": 3,
                    "difficulty": "Easy",
                    "tags": ["North Indian", "Sabzi", "Vegetarian", "Spinach", "Potato"],
                    "nutritional_info": {
                        "calories": "180 kcal per serving",
                        "protein": "6g",
                        "carbohydrates": "24g",
                        "fat": "7g",
                        "fiber": "5g",
                    },
                },
                {
                    "title": "Vegetarian Stuffed Capsicum with Spinach-Potato Filling",
                    "ingredients": [
                        {"name": "Capsicum", "quantity": "3 large, whole"},
                        {"name": "Potato", "quantity": "2 medium, boiled and mashed"},
                        {"name": "Paalak (Spinach)", "quantity": "100g, finely chopped"},
                        {"name": "Tomato", "quantity": "1 medium, finely chopped"},
                        {"name": "Oil", "quantity": "2 tbsp"},
                        {"name": "Salt", "quantity": "to taste"},
                        {"name": "Black pepper", "quantity": "1/2 tsp"},
                    ],
                    "instructions": [
                        "1. Cut the tops off the capsicums and remove seeds inside.",
                        "2. Heat oil in a pan, add chopped spinach and tomato, sauté until soft.",
                        "3. Add mashed potatoes, salt, and black pepper. Mix well to form a filling.",
                        "4. Stuff the capsicums with the prepared mixture.",
                        "5. Place stuffed capsicums in a greased pan, cover, and cook on low flame for 15–20 minutes until tender.",
                        "6. Serve warm with paratha or rice.",
                    ],
                    "region": "Fusion/Creative",
                    "dietary_preferences": "Vegetarian",
                    "prep_time_minutes": 20,
                    "cook_time_minutes": 25,
                    "servings": 3,
                    "difficulty": "Medium",
                    "tags": [
                        "Stuffed Vegetable",
                        "Creative",
                        "Vegetarian",
                        "Spinach",
                        "Potato",
                    ],
                    "nutritional_info": {
                        "calories": "210 kcal per serving",
                        "protein": "5g",
                        "carbohydrates": "28g",
                        "fat": "8g",
                        "fiber": "6g",
                    },
                },
            ]
        }

        # Validate and parse response
        # try:
        #     recipe_data = json.loads(response)
        # except json.JSONDecodeError:
        #     raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to parse recipe generation response.from LLM")
        
        recipe_data = response  # Using mock response for now
        
        recipe_suggestions = recipe_data.get("recipe_suggestions", [])
        if not recipe_suggestions:
            raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, "No recipes generated by LLM.")
        
        saved_recipes = []
        now = datetime.now(timezone.utc)
        
        for recipe in recipe_suggestions:
            # --- NEW: Step 1 - Prepare text for embedding ---
            # Combine the most semantically rich fields into a single string.
            
            ingredient_name = ", ".join([ing["name"] for ing in recipe.get("ingredients", [])])
            tags_str = ", ".join(recipe.get("tags", []))
            # print("Ingredient Names:", ingredient_name)
            # print("Tags:", tags_str)
            
            text_to_embed = (
                f"Title: {recipe.get('title', '')}. "
                f"Ingredients: {ingredient_name}. "
                f"Tags: {tags_str}. "
                f"Region: {recipe.get('region', '')}. "
                f"Dietary Preferences: {recipe.get('dietary_preferences', '')}. "
            )
            
            # print("Text to embed:", text_to_embed)
            
            # --- NEW: Step 2 - Generate the vector embedding ---
            """
            try:
                embedding_vector = await get_embedding(text_to_embed)
                recipe["vector_embedding"] = embedding_vector
            except Exception as e:
                raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Embedding generation failed: {str(e)}")
            """
            # For now, we'll skip embedding generation in this mock.
            
            validated = RecipeBase(
                **recipe
            )
            recipe_in_db = RecipeInDB(**validated.model_dump())
            recipe_in_db.createdAt = now
            recipe_in_db.updatedAt = now
            recipe_in_db.owner = ObjectId(current_user.id)    # Track Ownership
            
            result = await recipe_db.insert_one(recipe_in_db.model_dump(by_alias=True, exclude={"id"}))
            recipe_in_db.id = PyObjectId(result.inserted_id)
            saved_recipes.append(RecipePublic(**recipe_in_db.model_dump(by_alias=True)))
        
        return saved_recipes
    except Exception as e:
        if isinstance(e, ApiError):
            raise e
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Recipe generation failed: {str(e)}")
  

# --- Search Vector Embedding
@router.post("/search/vector", response_model=List[RecipePublic])
async def vector_search_recipe(
    request: VectorSearchRequest
):
    recipe_db = get_db()["recipes"]
    
    """
    Performs a semantic vector search for recipes based on a natural language query.
    """
    try:
        query_embedding = await get_embedding(request.query)
    except Exception as e:
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Could not process search query: {e}")
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "recipe_vector_index", # The name you gave your index in Atlas
                "path": "vector_embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": request.top_k
            }
        },
        # You can optionally project the search score if you want to use it
        # {
        #     "$project": {
        #         "score": {"$meta": "vectorSearchScore"},
        #         "document": "$$ROOT"
        #     }
        # }
    ]
    results = await recipe_db.aggregate(pipeline).to_list(length=request.top_k)
    return [RecipePublic.model_validate(res) for res in results]


# --- Filter Search ---
@router.post("/search", response_model=List[RecipePublic])
async def filtered_search_recipes(
    pagination: PaginationParams = Depends(get_pagination_params),
    title: Optional[str] = None,
    region: Optional[str] = None,
    difficulty: Optional[str] = None
):
    """
    Searches for recipes using filters for title, region, and difficulty. Supports pagination.
    """
    recipe_db = get_db()["recipes"]
    filter_query = {}
    
    if title:
        filter_query["title"] = {"$regex": title, "$options": "i"}
    if region:
        filter_query["region"] = {"$regex": region, "$options": "i"}
    if difficulty:
        filter_query["difficulty"] = {"$regex": difficulty, "$options": "i"}
    
    print("Filter: ", filter_query)
    
    cursor = recipe_db.find(filter_query).skip(pagination.skip).limit(pagination.limit)
    print("Cursor: ", cursor)
    result = await cursor.to_list(length=pagination.limit)
    print("result: ", result)
    return [RecipePublic.model_validate(res) for res in result]


# --- Recipe by ID ---
@router.get("/{recipe_id}", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def get_recipe_by_id(recipe_id: str):
    """
    Retrieves a single recipe by its unique ID.
    """
    recipe_db = get_db()["recipes"]
    try:
        if not ObjectId.is_valid(recipe_id):
            raise ApiError(status.HTTP_400_BAD_REQUEST, "Invalid recipe ID format.")
        
        # print("Recipe ID:", recipe_id)
        recipe = await recipe_db.find_one({"_id": ObjectId(recipe_id)})
        
        if not recipe:
            raise ApiError(status.HTTP_404_NOT_FOUND, "Recipe not found.")
        return RecipePublic(**recipe).model_dump(exclude={"vector_embedding", "owner"})
    except Exception as e:
        if isinstance(e, ApiError):
            raise e
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to fetch recipe: {str(e)}")
    

# --- Rate Recipe Endpoint ---
@router.post("/{recipe_id}/rate", response_model=RecipePublic, status_code=status.HTTP_200_OK)
async def rate_recipe(
    rating_request: RatingRequest,
    current_user: AuthenticatedUser,
    recipe_id: str,
):
    """
    Allows an authenticated user to rate a recipe.
    Submits a rating for a recipe. The average and count are updated atomically.
    """
    recipe_db = get_db()["recipes"] 
    try:
        if not ObjectId.is_valid(recipe_id):
            raise ApiError(status.HTTP_400_BAD_REQUEST, "Invalid recipe ID format.")
        
        recipe = await recipe_db.find_one({"_id": ObjectId(recipe_id)})
        if not recipe:
            raise ApiError(status.HTTP_404_NOT_FOUND, "Recipe not found.")
        
        # Prevent users from rating their own recipes
        '''
        if str(recipe.get("owner")) == current_user.id:
            raise ApiError(status.HTTP_403_FORBIDDEN, "You cannot rate your own recipe.")
        '''
        
        current_ratings = recipe.get("ratings", {"count": 0, "average": 0.0, "user_ratings": {}})
        user_ratings = current_ratings.get("user_ratings", {})
        
        # User Id
        user_id = str(current_user.id)
        previous_score = user_ratings.get(user_id)
        
        current_count = current_ratings.get("count", 0)
        current_average = current_ratings.get("average", 0.0)
        
        if previous_score is None:
            # New rating
            new_count = current_count + 1
            new_average = ((current_average * current_count) + rating_request.score) / new_count
        else:
            # Update existing rating
            new_count = current_count  # Count remains the same
            new_average = ((current_average * current_count) - previous_score + rating_request.score) / new_count
        
        
        user_ratings[user_id] = rating_request.score # Update or add the user's rating
        
        # Atomically update the recipe in the database
        updated_recipe = await recipe_db.find_one_and_update(
            {"_id": ObjectId(recipe_id)},
            {
                "$set": {
                    "ratings.average": round(new_average, 2), 
                    "ratings.user_ratings": user_ratings,
                    "ratings.count": new_count,
                    "updatedAt": datetime.now(timezone.utc)
                }
            },
            return_document=True
        )
        
        # Fetch the updated recipe
        return RecipePublic.model_validate(updated_recipe)
    
    except Exception as e:
        if isinstance(e, ApiError):
            raise e
        raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to rate recipe: {str(e)}")