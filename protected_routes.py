from fastapi import APIRouter, Depends
from supabase_auth.types import User

from auth_guard import UNAUTHORIZED_RESPONSE, get_current_user

router = APIRouter(prefix="/protected", tags=["protected"], responses=UNAUTHORIZED_RESPONSE)


@router.get("/profile", description="Returns the logged-in user's profile. Requires a Bearer token.")
def profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/dashboard", description="Returns the logged-in user's dashboard. Requires a Bearer token.")
def dashboard(user: User = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}!"}
