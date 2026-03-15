"""Supabase authentication utilities."""

import httpx
from functools import lru_cache
from fastapi import HTTPException, Request
from jose import jwt, jwk
from jose.exceptions import JOSEError
from api.config import get_settings


@lru_cache(maxsize=1)
def get_jwks(supabase_url: str) -> dict:
    """Fetch and cache JWKS from Supabase."""
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    try:
        response = httpx.get(jwks_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        # Return empty dict if JWKS fetch fails - will fall back to raising error
        return {"keys": []}


def get_signing_key(token: str, supabase_url: str):
    """Get the appropriate signing key for the token."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg")
    settings = get_settings()
    
    # For HS256, use the JWT secret directly
    if alg == "HS256":
        return settings.supabase_jwt_secret
    
    # For ES256/RS256, fetch from JWKS
    jwks = get_jwks(supabase_url)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwk.construct(key)
    
    raise ValueError(f"Unable to find signing key for kid: {kid}, alg: {alg}")


def get_user_id_from_token(request: Request) -> str:
    """
    Extract and validate user ID from Supabase JWT token.

    Args:
        request: FastAPI request object

    Returns:
        User ID (UUID string)

    Raises:
        HTTPException: If token is missing or invalid
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ")[1]
    settings = get_settings()

    try:
        # Get the appropriate signing key based on algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "HS256")
        signing_key = get_signing_key(token, settings.supabase_url)
        
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
