from pydantic import BaseModel, Field


class VectorSearchRequest(BaseModel):
    """Request model for performing a vector search."""
    query: str = Field(
        ...,
        description="Natural language search query, e.g., 'a light and healthy chicken dish for summer'",
        min_length=3
    )
    top_k: int = Field(
        5,
        gt=0,
        le=20,
        description="Number of similar recipes to return"
    )

class RatingRequest(BaseModel):
    """Request model for submitting a recipe rating."""
    score: float = Field(..., ge=0, le=5, description="The rating score between 0 and 5")