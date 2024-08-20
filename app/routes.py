from fastapi import APIRouter, Response
from app.agent import main, spokesman
from app.models import UserRequest, UserResponse, ResponseData, create_error_response
from datetime import datetime

router = APIRouter()

@router.post("/ask", response_model=UserResponse)
async def ask_question(request: UserRequest, response: Response):
    try:
        question = request.user_message
        spokesman.set_fastapi_response(response)
        qna_answer = await main(question)

        # Prepare the success response
        response_data = ResponseData(
            ticket_number=request.ticket_number,
            user_message=request.user_message,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qna_answer=qna_answer
        )
        user_response = UserResponse(
            response_code="200",
            response_message="success",
            error_message="",
            data=response_data
        )
        return user_response

    except SystemExit:
        # SystemExit is raised in ChainlitAssistantAgent's send method to return the response immediately
        response_data = ResponseData(
            ticket_number=request.ticket_number,
            user_message=request.user_message,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qna_answer=response.body.decode('utf-8')
        )
        user_response = UserResponse(
            response_code="200",
            response_message="success",
            error_message="",
            data=response_data
        )
        return user_response

    except Exception as e:
        # Handle other exceptions and return a formatted error response
        error_response = await create_error_response(
            ticket_number=request.ticket_number,
            user_message=request.user_message,
            error_message=str(e)
        )
        return error_response