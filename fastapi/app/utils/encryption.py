"""
API Key Encryption Utility

Encrypt/decrypt sensitive API keys in database
"""

from cryptography.fernet import Fernet
from app.core.config import settings
import base64


class APIKeyEncryption:
    """Encrypt and decrypt API keys"""

    def __init__(self):
        # Generate key from SECRET_KEY (should be 32 url-safe base64-encoded bytes)
        key = base64.urlsafe_b64encode(
            settings.SECRET_KEY.encode()[:32].ljust(32, b"0")
        )
        self.cipher = Fernet(key)

    def encrypt(self, api_key: str) -> str:
        """Encrypt API key"""
        if not api_key:
            return None
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        if not encrypted_key:
            return None
        return self.cipher.decrypt(encrypted_key.encode()).decode()


# Singleton instance
api_key_encryption = APIKeyEncryption()
