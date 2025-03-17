from fastapi import APIRouter
from ..schemas import HelloWorldRequest, HelloWorldResponse

# Create a router instance for our hello world endpoints
router = APIRouter()

@router.get("/", response_model=HelloWorldResponse)
async def hello_world() -> HelloWorldResponse:
    """
    Root endpoint that returns a simple hello world message.
    This serves as a template for creating additional endpoints.
    
    Returns:
        HelloWorldResponse: A simple hello world message
    """
    return HelloWorldResponse(message="Hello, World!")
