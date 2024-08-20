from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.models import JSONDecodeErrorResponse
from app.routes import router

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Check if the error is related to JSON decoding
    if exc.errors()[0]['type'] == 'json_invalid':
        error_response = JSONDecodeErrorResponse(
            error_message="JSON decode error: Expecting value"
        )
        return JSONResponse(
            status_code=422,
            content=error_response.dict()
        )
    
    # For other validation errors, return the default response
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Handle generic HTTP exceptions with a default error response format
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include the router that handles your routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)