from pwdlib import PasswordHash

# Initialize the modern handler
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return password_hash.verify(plain_password, hashed_password)
