from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

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

    # Token is present but not verified yet (verification comes next).
    return {"message": "Token received"}
