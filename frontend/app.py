import sys
from pathlib import Path
from typing import List
# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

import base64
import json
import os
import re
import time
import uuid
import atexit
import threading
from io import BytesIO
from PIL import Image
import numpy as np
from classes import User
import requests
import pandas as pd
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from classes import Session
from identity_utils import IdentityUtils
from dotenv import load_dotenv
import random
from utils.db_manager import DatabaseManager
import extra_streamlit_components as stx
from dotenv import load_dotenv
import rsa

load_dotenv()  # Load environment variables from .env file

# Helper functions for canvas operations
def save_canvas_changes(session_id, user_id):
    """Save pending changes to the database"""
    if "pending_changes" not in st.session_state:
        return
        
    # Process new objects
    for obj in st.session_state["pending_changes"].get("new", []):
        canvas_obj = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "object_data": json.dumps(obj),
            "created_by": user_id
        }
        db_manager.add_canvas_object(canvas_obj)
    
    # Process modified objects
    for obj_data in st.session_state["pending_changes"].get("modified", []):
        obj_id = obj_data["id"]
        obj = obj_data["object"]
        current_version = obj_data["version"]
        db_manager.edit_canvas_object(
            obj_id,
            json.dumps(obj),
            current_version + 1
        )
    
    # Process deleted objects
    for obj_data in st.session_state["pending_changes"].get("deleted", []):
        obj_id = obj_data["id"]
        current_version = obj_data["version"]
        db_manager.delete_canvas_object(obj_id, current_version + 1)
    
    # Clear pending changes
    st.session_state["pending_changes"] = {"new": [], "modified": [], "deleted": []}
    st.session_state["has_unsaved_changes"] = False

@st.dialog("Confirm Refresh")
def confirm_blank_canvas_refresh():
    """Dialog to confirm refreshing when canvas is blank in database"""
    st.write("The canvas has been cleared by another user. Your unsaved changes will be lost if you refresh.")
    if st.button("Refresh Anyway", key="confirm_refresh_button"):
        # Get the stored data
        db_objects = st.session_state.get("temp_refresh_data", {}).get("db_objects", [])
        
        # Update session state with fresh data
        st.session_state["canvas_objects"] = db_objects
        st.session_state["canvas_drawing_state"] = convert_db_objects_to_canvas_format(db_objects)
        
        # Clear pending changes
        st.session_state["pending_changes"] = {"new": [], "modified": [], "deleted": []}
        st.session_state["has_unsaved_changes"] = False
        
        st.success("Canvas refreshed with latest changes (blank canvas)")
        return True
    return False

def refresh_canvas_data(session_id):
    """Refresh canvas data from the database with confirmation if needed"""
    # First check if the database canvas is empty
    db_objects = db_manager.get_session_canvas_objects(session_id)
    
    # If canvas is empty in database and user has unsaved changes, confirm before proceeding
   
    # For normal refresh (non-empty canvas or no unsaved changes)
    st.session_state["canvas_objects"] = db_objects
    st.session_state["canvas_drawing_state"] = convert_db_objects_to_canvas_format(db_objects)


load_dotenv()

# Get a single instance of DatabaseManager to use throughout the app
db_manager = DatabaseManager()


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
        # Only store the IDs in session state, not the full objects
        st.session_state["canvas_object_ids"] = [obj.id for obj in db_manager.get_session_canvas_objects(session_id)]
        # Force a rerun to refresh the UI
        st.rerun()

def reset_canvas_state():
    """Reset all canvas-related session state variables"""
    # Clear canvas objects and drawing state
    st.session_state["canvas_objects"] = []
    st.session_state["canvas_drawing_state"] = {"objects": []}
    st.session_state["previous_canvas_state"] = []
    
    # Reset change tracking
    st.session_state["has_unsaved_changes"] = False
    st.session_state["pending_changes"] = {"new": [], "modified": [], "deleted": []}

def initialize_db_watcher():
    """Initialize the database watcher and canvas objects state."""
    #if "db_watcher" not in st.session_state:
        #st.session_state["db_watcher"] = setup_db_watcher(on_db_change)
    if "canvas_objects" not in st.session_state:
        st.session_state["canvas_objects"] = []
    if "previous_canvas_state" not in st.session_state:
        st.session_state["previous_canvas_state"] = []


def show_session_list():
    st.title("Available Drawing Sessions")
    
    
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
                if session_title:
                    # Create a new session in the database
                    user_id = st.session_state["identity_utils"].user_id
                    participants = [user_id]
                    participants.extend(invited_users)  # Add invited users to participants list
                    session_id = str(uuid.uuid4())
                    session = Session(id = session_id,title=session_title, width=canvas_width, height=canvas_height,participants=participants)
                    
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


            for participant in participants:
                session.participants.append(participant)
                st.text(f"  • {participant.display_name}")
            if st.button("Join Session", key=session.id):
                # First, reset any existing canvas state
                reset_canvas_state()
                refresh_canvas_data(session.id)
                
                # Then set the new session
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

def clean_duplicate_objects(session_id: str):
    """
    Remove duplicate objects from the database based on path data.
    This helps clean up objects that have been duplicated due to transform operations.
    """
    db_objects = db_manager.get_session_canvas_objects(session_id)
    
    # Group objects by their path data
    path_groups = {}
    for db_obj in db_objects:
        obj_data = json.loads(db_obj.object_data)
        if obj_data.get("type") == "path" and "path" in obj_data:
            path_key = json.dumps(obj_data.get("path"))
            if path_key not in path_groups:
                path_groups[path_key] = []
            path_groups[path_key].append(db_obj)
    
    # For each group of objects with the same path, keep only the one with the highest version
    for path_key, objs in path_groups.items():
        if len(objs) > 1:
            # Sort by version (descending)
            sorted_objs = sorted(objs, key=lambda x: x.version, reverse=True)
            # Keep the highest version, delete the rest
            for obj_to_delete in sorted_objs[1:]:
                db_manager.delete_canvas_object(obj_to_delete.id, obj_to_delete.version + 1)
    
    # Refresh canvas objects in session state
    st.session_state["canvas_objects"] = db_manager.get_session_canvas_objects(session_id)

def process_canvas_changes(canvas_result, session_id: str, user_id: str):
    """
    Process changes in canvas objects and track them for later saving.
    """
    if not canvas_result.json_data or "objects" not in canvas_result.json_data:
        return

    current_objects = canvas_result.json_data["objects"]
    previous_objects = st.session_state.get("previous_canvas_state", [])
    
    # Convert objects to dictionaries for easier comparison
    current_dict = {obj.get("id", str(i)): obj for i, obj in enumerate(current_objects)}
    previous_dict = {obj.get("id", str(i)): obj for i, obj in enumerate(previous_objects)}
    
    # Create path-based lookup for database objects
    path_to_db_obj = {}
    for db_obj in st.session_state.get("canvas_objects", []):
        obj_data = json.loads(db_obj.object_data)
        if obj_data.get("type") == "path" and "path" in obj_data:
            # Use path data as a key for lookup
            path_key = json.dumps(obj_data.get("path"))
            path_to_db_obj[path_key] = db_obj
    
    # Initialize pending changes if not already done
    if "pending_changes" not in st.session_state:
        st.session_state["pending_changes"] = {"new": [], "modified": [], "deleted": []}
    
    # Handle new and modified objects
    for obj_id, obj in current_dict.items():
        if obj_id not in previous_dict:
            # New object - add to pending changes
            st.session_state["pending_changes"]["new"].append(obj)
            st.session_state["has_unsaved_changes"] = True
        else:
            # Modified object - check if content changed
            prev_obj = previous_dict[obj_id]
            
            # Special handling for path objects
            if obj.get("type") == "path" and prev_obj.get("type") == "path" and "path" in obj and "path" in prev_obj:
                path_key = json.dumps(obj.get("path"))
                
                # If path data is the same but position/size changed, it's a transform operation
                if obj.get("path") == prev_obj.get("path") and (
                    obj.get("left") != prev_obj.get("left") or
                    obj.get("top") != prev_obj.get("top") or
                    obj.get("width") != prev_obj.get("width") or
                    obj.get("height") != prev_obj.get("height")
                ):
                    # Find the correct database object by path
                    if path_key in path_to_db_obj:
                        db_obj = path_to_db_obj[path_key]
                        # Add to pending changes
                        st.session_state["pending_changes"]["modified"].append({
                            "id": db_obj.id,
                            "object": obj,
                            "version": db_obj.version
                        })
                        st.session_state["has_unsaved_changes"] = True
                    else:
                        # Fallback if no matching path found
                        current_version = 1
                        for db_obj in st.session_state.get("canvas_objects", []):
                            if db_obj.id == obj_id:
                                current_version = db_obj.version
                                break
                        
                        # Add to pending changes
                        st.session_state["pending_changes"]["modified"].append({
                            "id": obj_id,
                            "object": obj,
                            "version": current_version
                        })
                        st.session_state["has_unsaved_changes"] = True
                # For other changes to path objects (actual path data changed)
                elif obj.get("path") != prev_obj.get("path"):
                    current_version = 1
                    for db_obj in st.session_state.get("canvas_objects", []):
                        if db_obj.id == obj_id:
                            current_version = db_obj.version
                            break
                    
                    # Add to pending changes
                    st.session_state["pending_changes"]["modified"].append({
                        "id": obj_id,
                        "object": obj,
                        "version": current_version
                    })
                    st.session_state["has_unsaved_changes"] = True
            # For non-path objects, use the existing comparison logic
            elif json.dumps(obj, sort_keys=True) != json.dumps(prev_obj, sort_keys=True):
                current_version = 1
                for db_obj in st.session_state.get("canvas_objects", []):
                    if db_obj.id == obj_id:
                        current_version = db_obj.version
                        break
                
                # Add to pending changes
                st.session_state["pending_changes"]["modified"].append({
                    "id": obj_id,
                    "object": obj,
                    "version": current_version
                })
                st.session_state["has_unsaved_changes"] = True
    
    # Handle deleted objects
    for obj_id in previous_dict:
        if obj_id not in current_dict:
            # Get current version for deletion
            current_version = 1
            for db_obj in st.session_state.get("canvas_objects", []):
                if db_obj.id == obj_id:
                    current_version = db_obj.version
                    break
            
            # Add to pending changes
            st.session_state["pending_changes"]["deleted"].append({
                "id": obj_id,
                "version": current_version
            })
            st.session_state["has_unsaved_changes"] = True
    
    # Update previous state for the next comparison
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
                if st.session_state["identity_utils"].has_identity:
                    st.markdown("🟢")
                else:
                    st.markdown("🔴")
            with col2:
                if st.session_state["identity_utils"].user_id:
                    st.write(f"User: {st.session_state['identity_utils'].user_id}")
                else:
                    st.write("Not connected")
            st.markdown("---")


@st.dialog("Clear Canvas")
def clear_canvas(session_id:str):
    st.write("Are you sure you want to clear the canvas? This action cannot be undone and will clear the entire canvas for all participants.")
    if st.button("Clear Canvas",key="clear_canvas_button"):
        # Clear all objects in the session
        db_manager.clear_canvas(session_id)
        st.success("Canvas cleared successfully!")
        #Refresh canvas objects in session state
        st.session_state["canvas_objects"] = db_manager.get_session_canvas_objects(session_id)
        st.session_state["canvas_drawing_state"] = convert_db_objects_to_canvas_format(st.session_state["canvas_objects"])

@st.dialog("Invite Participants")
def invite_participants(session_id:str,participants:List[User]):
    participant_ids = [p.id for p in participants]
    users = db_manager.get_all_users()
    st.write("Invite users to join the session.")
    # Placeholder for user selection (non-functional for now)
    selected_users = st.multiselect(
        "Select Users to Invite",
        options=[f"{u.id}:{u.display_name}" for u in users if u.id not in participant_ids ],
        default=[]
    )
    
    if st.button("Send Invites"):
        if selected_users:
            ids = [u.split(":")[0] for u in selected_users]
            names = [u.split(":")[1] for u in selected_users]
            result = db_manager.add_new_participants(session_id,user_ids=ids)
            st.success(f"Invites sent to: {', '.join(names)}")
        else:
            st.error("Please select at least one user to invite.")

#Canvas handling functionality
def full_app():
    # Get current user and session info
    user_id = st.session_state["identity_utils"].user_id
    session_id = st.session_state["selected_session"].id
    
    # Only fetch fresh objects from the database when needed
    # This prevents constant reloading that makes modals unusable
    if "canvas_objects" not in st.session_state or "canvas_drawing_state" not in st.session_state:
        db_objects = db_manager.get_session_canvas_objects(session_id)
        st.session_state["canvas_objects"] = db_objects
        st.session_state["canvas_drawing_state"] = convert_db_objects_to_canvas_format(db_objects)
    
    # Specify canvas parameters in application
    drawing_mode = st.sidebar.selectbox(
        "Drawing tool:",
        ("freedraw", "line", "rect", "circle", "polygon", "point"),
    )
    stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
    if drawing_mode == "point":
        point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)
    stroke_color = st.sidebar.color_picker("Stroke color hex: ")
    st.sidebar.markdown("### List of Participants")
    for p in st.session_state["selected_session"].participants:
        classify_p: User = p
        with st.sidebar.expander(f"User: {classify_p.display_name}"):
            st.text(f"User ID: {classify_p.id}")
            st.text(f"Created At: {classify_p.created_at}")
    new_participant_modal = st.sidebar.button("Invite Participants")
    if new_participant_modal:
        invite_participants(session_id,st.session_state["selected_session"].participants)

    if st.sidebar.button("Clear Canvas"):
        clear_canvas(session_id)
        
    # Add Save and Refresh buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.get("has_unsaved_changes", False):
            if st.button("💾 Save Changes", type="primary"):
                save_canvas_changes(session_id, user_id)
                # Refresh after saving
                refresh_canvas_data(session_id)
                st.success("Changes saved successfully!")
        else:
            st.button("💾 Save Changes", disabled=True)
            
    with col2:
        if st.button("🔄 Refresh Canvas"):
            if st.session_state.get("has_unsaved_changes", False):
                st.warning("You have unsaved changes that will be lost if you refresh. Save first or continue refreshing.")
            refresh_canvas_data(session_id)
            st.success("Canvas refreshed with latest changes!")
    
    # Show unsaved changes indicator if needed
    if st.session_state.get("has_unsaved_changes", False):
        st.warning("You have unsaved changes. Click 'Save Changes' to save them to the database.")
    
    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#eee",
        update_streamlit=True,
        height=st.session_state["selected_session"].height,
        width=st.session_state["selected_session"].width,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=False,
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
        # Use the session state canvas objects for display to ensure consistency
        if st.session_state["canvas_drawing_state"] and "objects" in st.session_state["canvas_drawing_state"]:
            objects = pd.json_normalize(st.session_state["canvas_drawing_state"]["objects"])
            for col in objects.select_dtypes(include=["object"]).columns:
                objects[col] = objects[col].astype("str")
            st.dataframe(objects)
        else:
            st.write("No canvas objects found.")

    ai_prompt = st.text_input("Have Claude 3.7 generate a drawing for you!")
    if st.button("Generate Drawing"):
        if ai_prompt:
            # Call the backend API to generate a drawing
            # For now, we will just show a success message
            st.success(f"Drawing generation queued: {ai_prompt}")
            generate_request_obj = {
                "user_id": st.session_state["identity_utils"].user_id,
                "session_id": st.session_state["selected_session"].id,
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
            # Create POST request to localhost:8000/generate, with signature as header
            headers = {
                "Authorization": f"Bearer {signature_b64}"
            }
            # Make the request to the backend API
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            response = requests.post(f"{backend_url}/generate", json=generate_request_obj, headers=headers)
            st.success(response.json().get("message", "Drawing generation request sent!"))  

        else:
            st.error("Please enter a prompt to generate a drawing.")





def cleanup_resources():
    """Clean up resources when the app is closing."""
    print("Cleaning up resources...")
    # Stop the watcher if it exists
    if "db_watcher" in st.session_state:
        try:
            st.session_state["db_watcher"].stop()
            st.session_state["db_watcher"].join()
            print("Database watcher stopped")
        except Exception as e:
            print(f"Error stopping database watcher: {e}")

if __name__ == "__main__":
    try:
        # Register cleanup handler
        atexit.register(cleanup_resources)
        
        st.title("Neurosketch")
        st.sidebar.subheader("Configuration")
        main()
    except Exception as e:
        # Stop the watcher if it exists
        cleanup_resources()
        raise e
