# --- Decorators ---
from functools import wraps

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from passlib.hash import bcrypt

from app.models import User


# Utility to inject user into template response
def _inject_user_context(result, request: Request, user: User):
    try:
        if hasattr(result, "context") and isinstance(result.context, dict):
            result.context["user"] = user
    except Exception as e:
        print("Failed to inject user context:", e)
    return result


def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user_id = request.session.get("user_id")

        if not user_id:
            login_url = request.url_for("user_login")
            return RedirectResponse(login_url, status_code=302)

        user = await User.get_or_none(id=user_id)

        if not user:
            raise HTTPException(status_code=403, detail="Niste ulogovani.")
        
        if not user.is_approved:
            raise HTTPException(status_code=403, detail="Korisnik nije odobren.")
        
        await user.fetch_related("game_player")

        request.state.user = user
        result = await func(request, *args, **kwargs)
        return _inject_user_context(result, request, user)

    return wrapper


def admin_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user_id = request.session.get("user_id")

        if not user_id:
            login_url = request.url_for("user_login")
            return RedirectResponse(login_url, status_code=302)

        user = await User.get_or_none(id=user_id)

        if not user or not user.is_admin or not user.is_approved:
            raise HTTPException(status_code=403, detail="Admin access required")

        await user.fetch_related("game_player")

        request.state.user = user
        result = await func(request, *args, **kwargs)
        return _inject_user_context(result, request, user)

    return wrapper


# --- Core Auth Logic ---


async def authenticate_user(username: str, password: str):
    """
    Authenticate and return a user only if credentials match and user is approved.
    """
    user = await User.get_or_none(username=username)
    if user and user.is_approved and bcrypt.verify(password, user.password_hash):
        return user
    return None


async def create_user(username: str, email: str, password: str):
    """
    Create a new user with hashed password and default approval = False.
    """
    hash_pw = bcrypt.hash(password)
    return await User.create(
        username=username,
        email=email,
        password_hash=hash_pw,
        is_admin=False,
        is_approved=False,
    )


# --- Utility ---


async def get_user_from_session(request: Request):
    """
    Return the currently logged-in user object, or None.
    """
    user_id = request.session.get("user_id")
    if user_id:
        return await User.get_or_none(id=user_id)
    return None
