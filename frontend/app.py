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
        page_title="Neurosketch", page_icon=":pencil2:"
    )

cookie_manager = stx.CookieManager()
key_for_cookie = "user_identity"
print(cookie_manager.get(key_for_cookie))
st.session_state["identity_utils"] = IdentityUtils(cookie_manager.get(key_for_cookie))

def on_db_change():
    print("Something changed in the database.")

def initialize_db_watcher():
    if "db_watcher" not in st.session_state:
        st.session_state["db_watcher"] = setup_db_watcher(on_db_change)


def show_session_list():
    st.title("Available Drawing Sessions")
    
    # Get user's sessions from database
    db_manager = DatabaseManager()
    user_id = st.session_state["identity_utils"].user_id
    sessions = db_manager.get_user_sessions(user_id)
    
    for session in sessions:
        with st.expander(f"📝 {session.title}"):
            st.text(f"Session ID: {session.id}")
            st.write("Participants:")
            # Get participants for this session
            participants = db_manager.get_session_participants(session.id)
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
                if st.session_state["identity_utils"].username:
                    st.write(f"User: {st.session_state['identity_utils'].username}")
                else:
                    st.write("Not connected")
            st.markdown("---")
            st.markdown(
                '<h6>Made in &nbsp<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" alt="Streamlit logo" height="16">&nbsp by <a href="https://twitter.com/andfanilo">@andfanilo</a></h6>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="margin: 0.75em 0;"><a href="https://www.buymeacoffee.com/andfanilo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a></div>',
                unsafe_allow_html=True,
            )


def full_app():

    with st.echo("below"):
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
        realtime_update = st.sidebar.checkbox("Update in realtime", True)

        # Create a canvas component
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color=bg_color,
            background_image=Image.open(bg_image) if bg_image else None,
            update_streamlit=realtime_update,
            height=150,
            drawing_mode=drawing_mode,
            point_display_radius=point_display_radius if drawing_mode == "point" else 0,
            display_toolbar=st.sidebar.checkbox("Display toolbar", True),
            key="full_app",
        )

        # Do something interesting with the image data and paths
        if canvas_result.image_data is not None:
            st.image(canvas_result.image_data)
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
