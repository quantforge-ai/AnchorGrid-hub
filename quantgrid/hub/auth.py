"""
QuantGrid Hub - API Key Authentication System

Generates and validates secure API keys for Hub contributors.
Format: qg_live_<64_char_hex>
"""

import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from loguru import logger

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class KeyGenerator:
    """
    Generates secure API keys with QuantGrid prefix.
    Format: qg_live_<64_char_hex>
    """
    
    PREFIX = "qg_live_"
    
    @staticmethod
    def generate() -> str:
        """
        Generate a new API key.
        
        Returns:
            Public key in format: qg_live_<random>
        """
        # Generate 32 bytes (64 hex chars) of random data
        raw_key = secrets.token_hex(32)
        public_key = f"{KeyGenerator.PREFIX}{raw_key}"
        
        logger.info(f"🔑 Generated new API key: {public_key[:20]}...")
        return public_key
    
    @staticmethod
    def hash_key(public_key: str) -> str:
        """
        Hash a key for secure storage.
        
        NEVER store raw keys in database. Always store this hash.
        If DB is compromised, user keys remain safe.
        
        Args:
            public_key: The public API key
            
        Returns:
            SHA256 hash of the key
        """
        return hashlib.sha256(public_key.encode()).hexdigest()
    
    @staticmethod
    def validate_format(public_key: str) -> bool:
        """Check if key has valid format"""
        if not public_key.startswith(KeyGenerator.PREFIX):
            return False
        
        # Should be prefix + 64 hex chars
        expected_length = len(KeyGenerator.PREFIX) + 64
        return len(public_key) == expected_length


async def get_current_user(
    api_key: str = Security(api_key_header),
    # db: Session = Depends(get_db)  # TODO: Inject real DB
):
    """
    The 'Bouncer' function - validates every Hub request.
    
    Args:
        api_key: API key from Authorization header
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException if invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ Missing API Key. Run 'quantgrid login' first."
        )
    
    # Remove 'Bearer ' prefix if present
    clean_key = api_key.replace("Bearer ", "").strip()
    
    # Validate format
    if not KeyGenerator.validate_format(clean_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="❌ Invalid API Key format"
        )
    
    # Hash the incoming key to match against DB
    hashed_input = KeyGenerator.hash_key(clean_key)
    
    # TODO: Replace with real DB lookup
    # user = db.query(User).filter(User.api_key_hash == hashed_input).first()
    # if user:
    #     return user
    
    # MOCK for testing
    MOCK_VALID_HASH = KeyGenerator.hash_key("qg_live_test_key_for_development_only_" + "0" * 32)
    
    if hashed_input == MOCK_VALID_HASH:
        return {
            "id": "test_user_id",
            "username": "test_developer",
            "role": "contributor"
        }
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="❌ Invalid API Key"
    )


def create_api_key_for_user(username: str) -> tuple[str, str]:
    """
    Create a new API key for a user.
    
    Args:
        username: Username
        
    Returns:
        Tuple of (public_key, hashed_key)
        Store hashed_key in DB, show public_key to user ONCE
    """
    public_key = KeyGenerator.generate()
    hashed_key = KeyGenerator.hash_key(public_key)
    
    logger.info(f"🔑 Created API key for user: {username}")
    
    return public_key, hashed_key
