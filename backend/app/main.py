import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
# from app.database.connection import connect_db, close_db_connection, get_db
from app.database.connection import MongoDB
from app.api import auth, user, recipe

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await MongoDB.connect_db()  # Connect and check the database
    
    # You can get the db instance here if needed for startup tasks like creating indexes
    db = MongoDB.get_db()
    # TODO: Create indexes on startup for better performance
    try:
        await db["users"].create_index("email", unique=True)
        await db["users"].create_index("username", unique=True)
        # await db["history"].create_index("user_email")
        print("MongoDB indexes created successfully.")
    except Exception as e:
        print(f"Error creating indexes: {e}")
    
    yield
    MongoDB.close_db_connection() # Close the connection when the app shuts down

app = FastAPI(
    title="DishGuru API",
    version="0.1.0",
    description="An AI-powered dish-suggester application",
    lifespan=lifespan
)

# API Routes
prestring = "/api/v1"

app.include_router(auth.router, prefix=f"{prestring}/auth")
app.include_router(user.router, prefix=f"{prestring}/user")
app.include_router(recipe.router, prefix=f"{prestring}/recipes")

@app.get("/")
async def root():
    return {"message": "Application running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)