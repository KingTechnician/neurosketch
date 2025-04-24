from fastapi import APIRouter,Header
from ..schemas import CanvasObject, GenerateRequest, GenerateResponse
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import rsa
import base64
import json
from utils.db_manager import DatabaseManager


import os

anthropic_key = os.getenv("ANTHROPIC_API_KEY")
load_dotenv()  # Load environment variables from .env file



router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest,authorization:str = Header(None)) -> GenerateResponse:
    print(request)
    print("Authorization Header:", authorization)
    #Split Bearer out of signature
    auth_signature = authorization.split(" ")[1]

    db=DatabaseManager()
    user = db.get_user(request.user_id)
    if not user:
        return GenerateResponse(
            status="error",
            message="User not found",
            data={},
            error="User not found"
        )
    # Verify the signature using the public key
    public_key = user.public_key
    try:
        # Decode the public key from base64
        public_key = rsa.PublicKey.load_pkcs1(public_key.encode())
        # Decode the base64 signature
        signature_bytes = base64.b64decode(auth_signature)
        # Convert request to the same format as was signed
        request_data = json.dumps(request.dict(), sort_keys=True)
        print("Request data being verified:", request_data)
        # Verify the signature
        rsa.verify(request_data.encode("utf-8"), signature_bytes, public_key)
        print("Signature verification successful!")
    except (rsa.VerificationError, ValueError, base64.binascii.Error) as e:
        print("Signature verification failed:", str(e))
        return GenerateResponse(
            status="error",
            message="Invalid signature",
            data={},
            error=str(e)
        )
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
