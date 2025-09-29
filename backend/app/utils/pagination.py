from fastapi import Query
from pydantic import BaseModel
from typing import Annotated

class PaginationParams(BaseModel):
    """Model for pagination query parameters."""
    skip: int
    limit: int
    
def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number starting from 1")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of items per page")] = 10
) -> PaginationParams:
    """
    FastAPI dependency to handle pagination parameters.
    Calculates the 'skip' value for database queries.
    """
    skip = (page - 1) * limit
    return PaginationParams(skip=skip, limit=limit)