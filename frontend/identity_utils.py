from pathlib import Path
import rsa
import json
import time
import streamlit as st
import extra_streamlit_components as stx
from extra_streamlit_components import CookieManager
from utils.db_manager import DatabaseManager

class IdentityUtils:
    def __init__(self,key_json):
        if not key_json:
            self.has_identity = False
            return
        
        self.key_file = Path("user_identity.json")
        self.user_id = key_json.get("user_id", None)
        self.private_key = key_json.get("private_key", None)
        
        # Check if we need to verify identity based on timestamp
        current_time = time.time()
        last_verified = st.session_state.get("last_identity_verification", 0)
        verification_interval = 5  # seconds
        
        if current_time - last_verified >= verification_interval:
            print(f"Verifying identity (last verified {current_time - last_verified:.1f}s ago)")
            self.has_identity = self._check_identity()
            # Store the verification result and timestamp
            st.session_state["identity_verified"] = self.has_identity
            st.session_state["last_identity_verification"] = current_time
        else:
            # Use the cached verification result
            self.has_identity = st.session_state.get("identity_verified", False)
            print(f"Using cached identity verification (verified {current_time - last_verified:.1f}s ago)")
    
    def _check_identity(self) -> bool:
        try:
            if not self.user_id or not self.private_key:
                return False
                
            # Load the private key
                
            # Load the private key
            private_key = rsa.PrivateKey.load_pkcs1(self.private_key.encode())
            
            # Verify identity using challenge-response
            db = DatabaseManager()
            is_verified = db.verify_user_identity(self.user_id, private_key)
            return is_verified
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error checking identity: {str(e)}")
            
            # Verify identity using challenge-response
            db = DatabaseManager()
            is_verified = db.verify_user_identity(self.user_id, private_key)
            return is_verified
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error checking identity: {str(e)}")
            return False
    
    def create_identity(self, user_id:str) -> None:
        (pubkey, privkey) = rsa.newkeys(2048)
        key_data = {
            "user_id": user_id,
            "private_key": privkey.save_pkcs1().decode()
        }
        self.username = user_id
        self.private_key = privkey
        return key_data


"""
def create_identity(username: str):
    (pubkey,privkey) = rsa.newkeys(2048)
    key_data = {    
        "username": username,
        "private_key": privkey.save_pkcs1().decode()
    }
    return key_data
"""
