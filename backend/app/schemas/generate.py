from pydantic import BaseModel

class GenerateRequest(BaseModel):
    """
    Schema for the Generate request.
    Defines the structure of the input parameters for the generation endpoint.
    """
    user_id:str
    timestamp:str
#    nonce:str
    signature:str
    prompt:str

class GenerateResponse(BaseModel):
    """
    Schema for the Generate response.
    Defines the structure of the output parameters for the generation endpoint.
    """
    status: str
    message: str
    data: dict = {}
    error: str = None