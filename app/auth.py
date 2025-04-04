from functools import wraps

from fastapi import Request
from fastapi.responses import RedirectResponse
from passlib.hash import bcrypt

from app.models import User

# --- Decorators ---


def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse("/login", status_code=302)
        user = await User.get_or_none(id=user_id)
        if not user or not user.is_approved:
            return RedirectResponse("/login", status_code=302)
        return await func(request, *args, **kwargs)

    return wrapper


def admin_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse("/login", status_code=302)
        user = await User.get_or_none(id=user_id)
        if not user or not user.is_admin or not user.is_approved:
            return RedirectResponse("/login", status_code=302)
        return await func(request, *args, **kwargs)

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


async def current_user(request: Request):
    """
    Return the currently logged-in user object, or None.
    """
    user_id = request.session.get("user_id")
    if user_id:
        return await User.get_or_none(id=user_id)
    return None
