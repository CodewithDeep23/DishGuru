from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from app.utils.exception import ApiError

load_dotenv()

MONGODB_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# client: AsyncIOMotorClient | None = None
# if MONGODB_URI:
#     client = AsyncIOMotorClient(MONGODB_URI)

if not MONGODB_URI or not DB_NAME:
        raise ApiError(500, "Database configuration environment variables not set.")

# def get_db():
#     if not MONGODB_URI or not DB_NAME:
#         raise ApiError(500, "Database configuration environment variables not set.")
#     if client is None:
#         raise ApiError(500, "Database client is not initialized.")
    
#     return client[DB_NAME]

# async def connect_db():
#     global client
    
#     if not MONGODB_URI:
#         raise ValueError("MONGODB_URI environment variable is not set.")
    
#     # global client, db
#     if client is None:
#         client = AsyncIOMotorClient(MONGODB_URI)
    
#     try:
#         await client.admin.command('ping')  # Check Connection
#         print("MongoDB connection established.")
#         # return client[DB_NAME]
#     except Exception as e:
#         print("MongoDB connection Error: ", e)
#         import sys
#         sys.exit(1)
#         # raise

# def close_db_connection():
#     """ Closes the MongoDB connection """
#     if client:
#         client.close()
#         print("MongoDB connection closed.")


class MongoDB:
    client: AsyncIOMotorClient | None = None

    @classmethod
    async def connect_db(cls):
        if cls.client is None:
            cls.client = AsyncIOMotorClient(MONGODB_URI)
        try:
            await cls.client.admin.command('ping')
            print("MongoDB connection established.")
        except Exception as e:
            print("MongoDB connection Error: ", e)
            import sys
            sys.exit(1)

    @classmethod
    def get_db(cls):
        if not cls.client:
            raise ApiError(500, "Database client is not initialized.")
        return cls.client[DB_NAME]
    
    @classmethod
    def close_db_connection(cls):
        if cls.client:
            cls.client.close()
            print("🔌 MongoDB connection closed")