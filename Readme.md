## DishSuggester - AI powered app

This is a mobile-first app where users snap pictures of available vegetables/fruits and receive regionally-relevant, chef-enriched recipe suggestions powered by image recognition and LLMs. The system stitches together a lightweight image inference pipeline (YOLOv8) and an LLM-driven recipe generation pipeline (OpenAI recommended) orchestrated by a FastAPI backend.


### Data Flow (sequence)
- App sends image + region → FastAPI endpoint /api/v1/scan.
- FastAPI stores image (S3/Equivalent) and forwards image to Inference Service.
- Inference Service returns ingredients JSON: [{name, confidence, bbox, amount_estimate}].
- FastAPI prepares prompt (fills template) and calls LLM API.
- LLM returns raw recipe text → FastAPI post-processes into JSON and enriches with blog tips (if available).
- Response returned to app → UI displays list of recipes with "Chef's Note".
- User selects recipe → App requests step-by-step "Cooking Mode" via /api/v1/recipes/{id}/cook, which returns instructions and TTS links or streams.
- App logs usage in MongoDB for personalization.

### Done
- User model, user routes, and authentication using JWT.
- Recipe model and api routes

### API Endpoints (Done)
`prefix: http://127.0.0.1:8000/api/v1`
#### Auth
- `/auth/register` -- Post: Registering user
- `/auth/login` -- Post: End-point for User login
- `/auth/logout` -- Post: End-point for logout

#### User
- `user/profile` -- Get: current user profile
- `user/favorite{recipe_id}` -- Get: current user favorite recipe using recipe_id
- `user/favorite{recipe_id}` -- Delete: Delete current user's recipe using recipe_id
- `user/my_recipes` -- Get: All recipe
- `user/favorites` -- Get: Get user favorites recipe

#### Recipes
- `recipes/generate` -- Post: Generate Recipe
- `recipes/search/vector` -- Post: Vector search recipe
- `recipes/search` -- Post: Filtered search recipe
- `recipes/{recipe_id}` -- Get: Get recipe by id
- `recipes/{recipe_id}/rate` -- Post: Rate recipe

#### Working: Not complete