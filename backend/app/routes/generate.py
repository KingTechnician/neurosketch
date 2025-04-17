from fastapi import APIRouter
from ..schemas import CanvasObject, GenerateRequest, GenerateResponse
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

import os

anthropic_key = os.getenv("ANTHROPIC_API_KEY")
load_dotenv()  # Load environment variables from .env file




router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    print(request)
    llm = ChatAnthropic(model="claude-3-5-haiku-20241022")

    structured_llm = llm.with_structured_output(CanvasObject)

    response = structured_llm.invoke(request.prompt)
    
    """
    Endpoint to handle generation requests.
    
    Args:
        request (GenerateRequest): The request object containing input parameters.
        
    Returns:
        GenerateResponse: The response object containing the status and generated data.
    """
    # Here you would typically call your generation logic
    # For now, we will return a mock response
    return GenerateResponse(
        status="success",
        message="Generation successful",
        data={**response},
    )