from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Request model
class UserRequest(BaseModel):
    ticket_number: str
    user_message: str

# Response Data model
class ResponseData(BaseModel):
    ticket_number: str
    user_message: str
    created_at: str
    qna_answer: Optional[str] = None

# Full Response model
class UserResponse(BaseModel):
    response_code: str = "200"
    response_message: str = "success"
    error_message: Optional[str] = ""
    data: Optional[ResponseData] = None

# Default Error Response model
class ErrorResponse(UserResponse):
    response_code: str = "11"
    response_message: str = "failed"
    error_message: str
    data: Optional[ResponseData] = None

class JSONDecodeErrorResponse(BaseModel):
    response_code: str = "11"
    response_message: str = "failed"
    error_message: str
    data: Optional[dict] = None

# Example of a function to create a default error response
async def create_error_response(ticket_number: str, user_message: str, error_message: str) -> ErrorResponse:
    return ErrorResponse(
        error_message=error_message,
        data=ResponseData(
            ticket_number=ticket_number,
            user_message=user_message,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qna_answer=None
        )
    )