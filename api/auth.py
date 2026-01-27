"""Supabase authentication utilities."""

from fastapi import HTTPException, Request
from jose import jwt, JWTError
from api.config import get_settings


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
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
