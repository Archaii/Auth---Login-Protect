from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from supabase_auth.errors import AuthError

from supabase_client import new_client

router = APIRouter(prefix="/protected", tags=["protected"])


def extract_bearer_token(authorization: str | None):
    """Return the token from an "Authorization: Bearer <token>" header, or None.

    None means the header is missing, uses another scheme, or has no token.
    """
    if not authorization:
        return None

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


@router.get("/profile", description="Returns the logged-in user's profile. Requires a Bearer token.")
def profile(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)

    if token is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Access token required"},
        )

    # Ask Supabase whether the token is real. This is a network call, so an
    # expired, tampered, or forged token is rejected by Supabase itself.
    try:
        response = new_client().auth.get_user(token)
    except AuthError:
        response = None

    if response is None or response.user is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"},
        )

    user = response.user

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }
