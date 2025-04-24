import sys
from pathlib import Path
# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

import base64
import json
import os
import re
import time
import uuid
from io import BytesIO
from PIL import Image
import numpy as np
import requests
import pandas as pd
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from classes import Session
from identity_utils import IdentityUtils
from dotenv import load_dotenv
from utils.db_manager import DatabaseManager
from utils.db_watcher import setup_db_watcher
import extra_streamlit_components as stx
import rsa


load_dotenv()


st.set_page_config(
        page_title="Neurosketch", page_icon=":pencil2:",layout="wide",
    )






cookie_manager = stx.CookieManager()
key_for_cookie = "user_identity"
st.session_state["identity_utils"] = IdentityUtils(cookie_manager.get(key_for_cookie))

def convert_db_objects_to_canvas_format(db_objects):
    """Convert CanvasObjectDB objects to canvas-compatible format"""
    canvas_objects = []
    for obj in db_objects:
        # Parse object_data JSON string back to dict
        canvas_obj = json.loads(obj.object_data)
        # Ensure object has correct ID
        canvas_obj["id"] = obj.id
        canvas_objects.append(canvas_obj)
    return {"objects": canvas_objects}

def on_db_change():
    """Handle database changes by updating in-memory canvas objects and refreshing the UI."""
    if "selected_session" in st.session_state and st.session_state["selected_session"]:
        session_id = st.session_state["selected_session"].id
        db_manager = DatabaseManager()
        latest_objects = db_manager.get_session_canvas_objects(session_id)
        st.session_state["canvas_objects"] = latest_objects
        # Convert to canvas format and store for next render
        st.session_state["canvas_drawing_state"] = convert_db_objects_to_canvas_format(latest_objects)
        st.rerun()

def initialize_db_watcher():
    """Initialize the database watcher and canvas objects state."""
    if "db_watcher" not in st.session_state:
        st.session_state["db_watcher"] = setup_db_watcher(on_db_change)
    if "canvas_objects" not in st.session_state:
        st.session_state["canvas_objects"] = []
    if "previous_canvas_state" not in st.session_state:
        st.session_state["previous_canvas_state"] = []


def show_session_list():
    st.title("Available Drawing Sessions")
    
    db_manager = DatabaseManager()
    
    # Add new session expander
    with st.expander("Start a new Session"):
        with st.form("new_session_form"):
            session_title = st.text_input("Session Title")
            # Placeholder multiselect for inviting users (non-functional for now)
            invited_users = st.multiselect(
                "Invite Users",
                options=["User 1", "User 2", "User 3"],  # Placeholder options
                default=[]
            )
            col1, col2 = st.columns(2)
            with col1:
                canvas_width = st.number_input("Canvas Width", min_value=100, value=1000)
            with col2:
                canvas_height = st.number_input("Canvas Height", min_value=100, value=1000)
            
            # Submit button (no functionality yet)
            submitted = st.form_submit_button("Create Session")

            if submitted:
                print("Creating new session...")
                if session_title:
                    # Create a new session in the database
                    user_id = st.session_state["identity_utils"].user_id
                    participants = [user_id]
                    participants.extend(invited_users)  # Add invited users to participants list
                    session_id = str(uuid.uuid4())
                    session = Session(id = session_id,title=session_title, width=canvas_width, height=canvas_height,participants=participants)
                    print(session)
                    db_manager.create_session(session)
                    
                    st.success(f"Session '{session_title}' created successfully!")
    
    # Get user's sessions from database
    user_id = st.session_state["identity_utils"].user_id
    sessions = db_manager.get_user_sessions(user_id)

    if not sessions:
        st.warning("No sessions available. Create a new session to get started with drawing!")
    
    for session in sessions:
        with st.expander(f"📝 {session.title}"):
            st.text(f"Session ID: {session.id}")
            st.write("Participants:")
            # Get participants for this session
            participants = db_manager.get_session_participants(session.id)

            print(participants)

            for participant in participants:
                st.text(f"  • {participant.display_name}")
            if st.button("Join Session", key=session.id):
                st.session_state["selected_session"] = session
                st.session_state["show_canvas"] = True
                st.rerun()

def create_identity(username: str):
    (pubkey,privkey) = rsa.newkeys(2048)
    key_data = {    
        "username": username,
        "private_key": privkey.save_pkcs1().decode()
    }
    return key_data

def disable(b):
    st.session_state["login_button_disabled"] = b

def handle_identity_creation():
    st.session_state["identity_created"] = True
    st.session_state["login_button_disabled"] = True

def show_identity_creation():
    st.warning("⚠️ New User Detected! You need to create an identity to use Neurosketch.")
    display_name = st.text_input("Enter your display name:")
    
    if st.button("Create Identity", disabled=st.session_state["login_button_disabled"]):
        if display_name:
            user_id = str(uuid.uuid4())
            key_data = st.session_state["identity_utils"].create_identity(user_id)
            
            # Create anonymous user in database first
            db_manager = DatabaseManager()
            private_key = rsa.PrivateKey.load_pkcs1(key_data["private_key"].encode("utf-8"))
            public_key = rsa.PublicKey(n=private_key.n,e=private_key.e)
            public_key = public_key.save_pkcs1().decode("utf-8")
            db_manager.create_anonymous_user(user_id,public_key,display_name)
            
            # Set the cookie before any state changes or reruns
            cookie_manager.set(key_for_cookie, json.dumps(key_data), key="cookie", expires_at=None)
            
            # Show the key data
            st.json(key_data)
            st.success("Identity created successfully! You will be redirected in a moment...")
            
            # Trigger single rerun after everything is complete
            time.sleep(2)  # Give user time to see the success message
            st.rerun()
        else:
            st.error("Please enter a display name")

def process_canvas_changes(canvas_result, session_id: str, user_id: str):
    """
    Process changes in canvas objects and update the database accordingly.
    Handles additions, modifications, and deletions with proper versioning.
    """
    if not canvas_result.json_data or "objects" not in canvas_result.json_data:
        return

    current_objects = canvas_result.json_data["objects"]
    previous_objects = st.session_state.get("previous_canvas_state", [])
    
    # Convert objects to dictionaries for easier comparison
    current_dict = {obj.get("id", str(i)): obj for i, obj in enumerate(current_objects)}
    previous_dict = {obj.get("id", str(i)): obj for i, obj in enumerate(previous_objects)}
    
    db_manager = DatabaseManager()
    
    # Handle new and modified objects
    for obj_id, obj in current_dict.items():
        if obj_id not in previous_dict:
            # New object
            canvas_obj = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "object_data": json.dumps(obj),
                "created_by": user_id
            }
            db_manager.add_canvas_object(canvas_obj)
        else:
            # Modified object - check if content changed
            prev_obj = previous_dict[obj_id]
            if json.dumps(obj, sort_keys=True) != json.dumps(prev_obj, sort_keys=True):
                # Get current version and increment
                current_version = 1  # Default for new objects
                for db_obj in st.session_state.get("canvas_objects", []):
                    if db_obj.id == obj_id:
                        current_version = db_obj.version
                        break
                
                db_manager.edit_canvas_object(
                    obj_id,
                    json.dumps(obj),
                    current_version + 1
                )
    
    # Handle deleted objects
    for obj_id in previous_dict:
        if obj_id not in current_dict:
            # Get current version and increment for deletion
            current_version = 1
            for db_obj in st.session_state.get("canvas_objects", []):
                if db_obj.id == obj_id:
                    current_version = db_obj.version
                    break
            
            db_manager.delete_canvas_object(obj_id, current_version + 1)
    
    # Update previous state
    st.session_state["previous_canvas_state"] = current_objects

def main():
    # Initialize database watcher and canvas state
    initialize_db_watcher()
    
    if "button_id" not in st.session_state:
        st.session_state["button_id"] = ""
    if "color_to_label" not in st.session_state:
        st.session_state["color_to_label"] = {}
    if "selected_session" not in st.session_state:
        st.session_state["selected_session"] = None
    if "show_canvas" not in st.session_state:
        st.session_state["show_canvas"] = False
    if "identity_utils" not in st.session_state:
        st.session_state["identity_utils"] = IdentityUtils()
    if "login_button_disabled" not in st.session_state:
        st.session_state["login_button_disabled"] = False

    # Gate all content behind identity check
    if not st.session_state["identity_utils"].has_identity:
        show_identity_creation()
    else:
        # Only show app content if identity exists
        if not st.session_state["show_canvas"]:
            show_session_list()
        else:
            st.title(f"Drawing Session: {st.session_state['selected_session'].title}")
            if st.button("← Back to Sessions"):
                st.session_state["show_canvas"] = False
                st.session_state["selected_session"] = None
                st.rerun()
            full_app()

    if st.session_state["show_canvas"]:
        with st.sidebar:
            # Add connection status at top of sidebar
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown("🔴")  # Red circle for disconnected
            with col2:
                if st.session_state["identity_utils"].user_id:
                    st.write(f"User: {st.session_state['identity_utils'].user_id}")
                else:
                    st.write("Not connected")
            st.markdown("---")


def full_app():
    # Get current user and session info
    user_id = st.session_state["identity_utils"].user_id
    session_id = st.session_state["selected_session"].id
    
    # Get current session's objects from database if not in state
    if "canvas_drawing_state" not in st.session_state:
        db_manager = DatabaseManager()
        db_objects = db_manager.get_session_canvas_objects(session_id)
        st.session_state["canvas_objects"] = db_objects
        st.session_state["canvas_drawing_state"] = convert_db_objects_to_canvas_format(db_objects)
    
    # Specify canvas parameters in application
    drawing_mode = st.sidebar.selectbox(
        "Drawing tool:",
        ("freedraw", "line", "rect", "circle", "transform", "polygon", "point"),
    )
    stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
    if drawing_mode == "point":
        point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)
    stroke_color = st.sidebar.color_picker("Stroke color hex: ")
    bg_color = st.sidebar.color_picker("Background color hex: ", "#eee")
    bg_image = st.sidebar.file_uploader("Background image:", type=["png", "jpg"])

    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color=bg_color,
        background_image=Image.open(bg_image) if bg_image else None,
        update_streamlit=True,
        height=1000,
        width=1000,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=st.sidebar.checkbox("Display toolbar", True),
        key="canvas_app",
        initial_drawing=st.session_state.get("canvas_drawing_state", {"objects": []})
    )
    
    # Process any changes to canvas objects
    if canvas_result.json_data is not None:
        process_canvas_changes(canvas_result, session_id, user_id)

    
    # Do something interesting with the image data and paths
    #if canvas_result.image_data is not None:
    #    st.image(canvas_result.image_data)
    with st.expander("Canvas Data"):
        if canvas_result.json_data is not None:
            objects = pd.json_normalize(canvas_result.json_data["objects"])
            for col in objects.select_dtypes(include=["object"]).columns:
                objects[col] = objects[col].astype("str")
            st.dataframe(objects)

    ai_prompt = st.text_input("Have Claude 3.7 generate a drawing for you!")
    if st.button("Generate Drawing"):
        if ai_prompt:
            # Call the backend API to generate a drawing
            # For now, we will just show a success message
            st.success(f"Drawing generation queued: {ai_prompt}")
            generate_request_obj = {
                "user_id": st.session_state["identity_utils"].user_id,
                "timestamp": str(time.time()),
                "prompt": ai_prompt
            }
            # Convert to string in a consistent way
            request_data = json.dumps(generate_request_obj, sort_keys=True)
            private_key = rsa.PrivateKey.load_pkcs1(st.session_state["identity_utils"].private_key.encode("utf-8"))
            # Sign the actual request data
            signature = rsa.sign(request_data.encode("utf-8"), private_key, "SHA-256")
            # Convert signature to base64 string
            signature_b64 = base64.b64encode(signature).decode("utf-8")
            print("Request data being signed:", request_data)
            print("Signature:", signature_b64)
            # Create POST request to localhost:8000/generate, with signature as header
            headers = {
                "Authorization": f"Bearer {signature_b64}"
            }
            # Make the request to the backend API
            response = requests.post("http://localhost:8000/generate", json=generate_request_obj, headers=headers)
            print("Response:", response.json())

        else:
            st.error("Please enter a prompt to generate a drawing.")





if __name__ == "__main__":
    try:
        st.title("Neurosketch")
        st.sidebar.subheader("Configuration")
        main()
    except Exception as e:
        # Stop the watcher if it exists
        if "db_watcher" in st.session_state:
            st.session_state["db_watcher"].stop()
            st.session_state["db_watcher"].join()
        raise e
