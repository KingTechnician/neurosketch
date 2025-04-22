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


print(st.session_state)





cookie_manager = stx.CookieManager()
key_for_cookie = "user_identity"
st.session_state["identity_utils"] = IdentityUtils(cookie_manager.get(key_for_cookie))

def on_db_change():
    print("Something changed in the database.")

def initialize_db_watcher():
    if "db_watcher" not in st.session_state:
        st.session_state["db_watcher"] = setup_db_watcher(on_db_change)


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
    
    # Show success message if identity was just created
    if st.session_state.get("identity_created", False):
        st.success("🔑 Identity created! Important: Never delete your key file (user_identity.json) or you will lose access to your account.")
        if st.session_state.get("identity_key_data"):
            st.json(st.session_state["identity_key_data"])
            # Set cookie after showing messages
            cookie_manager.set(key_for_cookie, json.dumps(st.session_state["identity_key_data"]), key="cookie", expires_at=None)
            # Reset the state
            st.session_state["identity_created"] = False
            st.session_state["identity_key_data"] = None
            st.rerun()
    
    if st.button("Create Identity", disabled=st.session_state["login_button_disabled"]):
        if display_name:
            user_id = str(uuid.uuid4())
            key_data = st.session_state["identity_utils"].create_identity(user_id)
            # Store key data in session state
            cookie_manager.set(key_for_cookie, json.dumps(key_data), key="cookie", expires_at=None)
            # Create anonymous user in database
            db_manager = DatabaseManager()
            db_manager.create_anonymous_user(user_id,display_name)
            # Set flags and trigger rerun
            st.session_state["identity_created"] = True
            st.session_state["login_button_disabled"] = True
            st.rerun()
        else:
            st.error("Please enter both username and display name")

def main():
    # Initialize database watcher once
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
    if "identity_created" not in st.session_state:
        st.session_state["identity_created"] = False
    if "identity_key_data" not in st.session_state:
        st.session_state["identity_key_data"] = None
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
    )

    
    # Do something interesting with the image data and paths
    #if canvas_result.image_data is not None:
    #    st.image(canvas_result.image_data)
    if canvas_result.json_data is not None:
        objects = pd.json_normalize(canvas_result.json_data["objects"])
        for col in objects.select_dtypes(include=["object"]).columns:
            objects[col] = objects[col].astype("str")
        st.dataframe(objects)





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
