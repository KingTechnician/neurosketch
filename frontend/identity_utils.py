from pathlib import Path
import rsa
import json

class IdentityUtils:
    def __init__(self):
        self.key_file = Path("user_identity.json")
        self.username = None
        self.private_key = None
        self.has_identity = self._check_identity()
    
    def _check_identity(self) -> bool:
        if not self.key_file.exists():
            return False
            
        try:
            key_data = json.loads(self.key_file.read_text())
            if "username" not in key_data or "private_key" not in key_data:
                return False
            private_key = rsa.PrivateKey.load_pkcs1(key_data["private_key"].encode())
            self.username = key_data["username"]
            self.private_key = private_key
            return True
        except (json.JSONDecodeError, ValueError, TypeError):
            return False
    
    def create_identity(self, username: str) -> None:
        (pubkey, privkey) = rsa.newkeys(2048)
        key_data = {
            "username": username,
            "private_key": privkey.save_pkcs1().decode()
        }
        self.key_file.write_text(json.dumps(key_data))
        self.username = username
        self.private_key = privkey
