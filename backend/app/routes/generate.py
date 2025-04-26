from fastapi import APIRouter,Header
from ..schemas import CanvasObject, GenerateRequest, GenerateResponse,setup_langchain_parser,create_prompt_template
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import rsa
import base64
import uuid
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
    session = db.get_session(request.session_id)
    session_objects =[json.loads(d.object_data) for d in db.get_session_canvas_objects(request.session_id)]
    session_objects = [CanvasObject.from_dict(obj) for obj in session_objects]
    existing_objects = "\n".join([obj.model_dump_json() for obj in session_objects])
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
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

    system_prompt = """
    You are an assistant that has the goal of drawing Fabric.js components in a canvas.

    You will be given the following information:

    - The canvas width and height
    - The object definition (type, position, size, color, etc.)
    - The prompt that describes the object to be drawn
    - Any existing objects in the canvas (if any)

    Be sure that you are fitting as many required properties as possible in the object definition. There are typings for each of the properties that you *must use*.

    **Use only M, L, Q, and Z command for the path.**
    **Always include width and height in the object definition.**
    Prompt: {prompt}
    Canvas Width: {width}
    Canvas Height: {height}
    Existing objects: {existing_objects}

    """
    # Create the request with the system prompt and user prompt
    system_prompt = system_prompt.format(
        prompt=request.prompt,
        width=session.width,
        height=session.height,
        existing_objects=existing_objects
    )

    parser,format_instructioins = setup_langchain_parser()
    prompt_template = create_prompt_template(format_instructioins)

    prompt_and_model = prompt_template | llm | parser
    response = prompt_and_model.invoke({"description": request.prompt, "width": session.width, "height": session.height})
    object_data = response.to_dict()
    canvas_register = {
        "id": str(uuid.uuid4()),
        "session_id": request.session_id,
        "object_data": json.dumps(object_data),
        "created_by": request.user_id,
    }
    for key,value in canvas_register.items():
        print(type(value))
    db.add_canvas_object(canvas_register)

    
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
        data={},
    )
