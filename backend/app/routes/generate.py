from fastapi import APIRouter, Header, Request
from ..schemas import CanvasObject, GenerateRequest, GenerateResponse, setup_langchain_parser, create_prompt_template
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import rsa
import base64
import uuid
import json
import socket
import threading
from utils.db_manager import DatabaseManager

import os

# Load environment variables at module level
load_dotenv()  # Load environment variables from .env file
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

router = APIRouter()

def get_worker_info():
    """Get information about the current worker (backend server)"""
    hostname = socket.gethostname()
    try:
        ip_address = socket.gethostbyname(hostname)
    except:
        ip_address = "127.0.0.1"
    return f"Worker-{hostname} ({ip_address})"

def process_in_background(request, auth_signature, client_info):
    """Process the generation request in a background thread"""
    worker_info = get_worker_info()
    print(f"[WORKER LOG] Starting processing request from {client_info} on {worker_info}")
    
    try:
        # Use the singleton instance of DatabaseManager
        db = DatabaseManager()
        user = db.get_user(request.user_id)
        session = db.get_session(request.session_id)
        
        # Verify the signature using the public key
        public_key = user.public_key
        try:
            # Decode the public key from base64
            public_key = rsa.PublicKey.load_pkcs1(public_key.encode())
            # Decode the base64 signature
            signature_bytes = base64.b64decode(auth_signature)
            # Convert request to the same format as was signed
            request_data = json.dumps(request.dict(), sort_keys=True)
            # Verify the signature
            rsa.verify(request_data.encode("utf-8"), signature_bytes, public_key)
            print(f"[WORKER LOG] Signature verification successful for request from {client_info}")
        except Exception as e:
            print(f"[WORKER LOG] Signature verification failed: {str(e)}")
            return
        
        # Get existing canvas objects
        session_objects = [json.loads(d.object_data) for d in db.get_session_canvas_objects(request.session_id)]
        session_objects = [CanvasObject.from_dict(obj) for obj in session_objects]
        existing_objects = "\n".join([obj.model_dump_json() for obj in session_objects])
        
        # Set up the LLM
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
        
        # Create the system prompt
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
        
        # Format the system prompt
        system_prompt = system_prompt.format(
            prompt=request.prompt,
            width=session.width,
            height=session.height,
            existing_objects=existing_objects
        )
        
        # Set up the parser and prompt template
        parser, format_instructions = setup_langchain_parser()
        prompt_template = create_prompt_template(format_instructions)
        
        # Generate the response
        prompt_and_model = prompt_template | llm | parser
        response = prompt_and_model.invoke({"description": request.prompt, "width": session.width, "height": session.height})
        object_data = response.to_dict()
        
        # Create canvas object
        canvas_register = {
            "id": str(uuid.uuid4()),
            "session_id": request.session_id,
            "object_data": json.dumps(object_data),
            "created_by": request.user_id,
        }
        
        # Add to database
        db.add_canvas_object(canvas_register)
        
        # Log completion
        print(f"[WORKER LOG] Task completed by {worker_info} for client {client_info}")
        
    except Exception as e:
        print(f"[WORKER LOG] Error in background processing: {str(e)}")

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, authorization: str = Header(None), request_obj: Request = None) -> GenerateResponse:
    """
    Endpoint to handle generation requests.
    
    Args:
        request (GenerateRequest): The request object containing input parameters.
        authorization (str): Authorization header with signature.
        request_obj (Request): FastAPI request object to get client information.
        
    Returns:
        GenerateResponse: The response object containing the status and generated data.
    """
    # Get client information
    client_ip = request_obj.client.host
    client_info = f"Client ({client_ip})"
    
    # Get worker information
    worker_info = get_worker_info()
    
    # Log request receipt
    print(f"[WORKER LOG] Request received from {client_info} by {worker_info}")
    
    # Basic validation before accepting the task
    if not authorization:
        return GenerateResponse(
            status="error",
            message="Missing authorization header",
            data={},
            error="Authorization header is required"
        )
    
    auth_signature = authorization.split(" ")[1]
    
    # Verify user exists
    db = DatabaseManager()
    user = db.get_user(request.user_id)
    if not user:
        return GenerateResponse(
            status="error",
            message="User not found",
            data={},
            error="User not found"
        )
    
    # Start a background thread for processing
    thread = threading.Thread(
        target=process_in_background,
        args=(request, auth_signature, client_info),
        daemon=True
    )
    thread.start()
    
    # Return immediate response with both client and worker info
    task_id = str(uuid.uuid4())
    return GenerateResponse(
        status="processing",
        message=f"Request from {client_info} accepted by {worker_info} - Processing in background",
        data={
            "client": client_ip,
            "worker": worker_info,
            "task_id": task_id
        },
    )
