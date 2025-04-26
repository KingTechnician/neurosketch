from pathlib import Path
import rsa
import json
import extra_streamlit_components as stx
from extra_streamlit_components import CookieManager
from utils.db_manager import DatabaseManager

class IdentityUtils:
    def __init__(self,key_json):
        if not key_json:
            self.has_identity = False
            return
        print("Initializing IdentityUtils")
        print(type(key_json))
        self.key_file = Path("user_identity.json")
        self.user_id = key_json.get("user_id", None)
        self.private_key = key_json.get("private_key", None)
        print("Checking if this is running")
        self.has_identity = self._check_identity()
    
    def _check_identity(self) -> bool:
        print("Checking identity of", self.user_id) 
        try:
            if not self.user_id or not self.private_key:
                return False
                
            # Load the private key
            private_key = rsa.PrivateKey.load_pkcs1(self.private_key.encode())
            
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