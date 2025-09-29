from fastapi import HTTPException
from typing import Dict, Any

class ApiError(HTTPException):
    def __init__(self, status_code: int, message: str, headers: Dict[str, Any] | None = None):
        super().__init__(
            status_code=status_code, 
            detail={"success": False, "message": message},
            headers=headers
        )