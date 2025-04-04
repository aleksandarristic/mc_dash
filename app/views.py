import os

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import app.config
from app.auth import admin_required, create_user, current_user, login_required
from app.cache import get_server_status
from app.models import ServerSnapshot, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
@login_required
async def homepage(request: Request):
    # Get live server status from in-memory cache
    status = get_server_status()

    # List available downloads
    download_dir = app.config.DOWNLOADS_DIR
    downloads = (
        [
            f
            for f in os.listdir(download_dir)
            if os.path.isfile(os.path.join(download_dir, f))
        ]
        if os.path.exists(download_dir)
        else []
    )

    # Static server info (config-based)
    server_info = {
        "ip": app.config.SERVER_IP,
        "version": app.config.SERVER_VERSION,
        "motd": app.config.SERVER_MOTD,
    }

    # Last few historical snapshots for context (optional)
    snapshots = await ServerSnapshot.all().order_by("-timestamp").limit(5)
    user = await current_user(request)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "server_status": status["status"],
            "players_online": status["players_online"],
            "max_players": status["max_players"],
            "online_names": status["player_names"],
            "server_info": server_info,
            "downloads": downloads,
            "snapshots": snapshots,
            "user": user,
        },
    )


### USER LOGIN AND REGISTRATION


@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    existing_user = await User.get_or_none(username=username)
    if existing_user:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Username already exists"}
        )

    await create_user(username, email, password)
    return templates.TemplateResponse(
        "login.html", {"request": request, "message": "User registered successfully!"}
    )


@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_user(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    user = await User.get_or_none(username=username)
    if not user or not user.verify_password(password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials"}
        )
    if not user.is_approved:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "User not approved"}
        )

    # log the user in
    request.session["user_id"] = user.id

    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


# ADMIN ROUTES - MOVE TO ANOTHER APP


@router.get("/admin")
@admin_required
async def admin_dashboard(request: Request):
    user = await current_user(request)

    return templates.TemplateResponse("admin.html", {"request": request, "user": user})


@router.get("/admin/users")
@admin_required
async def user_list(request: Request):
    users = await User.all().order_by("created_at")
    user = await current_user(request)
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users, "user": user},
    )


@router.post("/admin/approve/{user_id}")
@admin_required
async def approve_user(request: Request, user_id: int):
    user = await User.get_or_none(id=user_id)
    if user:
        user.is_approved = True
        await user.save()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/admin/promote/{user_id}")
@admin_required
async def promote_user(request: Request, user_id: int):
    user = await User.get_or_none(id=user_id)
    if user:
        user.is_admin = True
        await user.save()
    return RedirectResponse("/admin/users", status_code=302)
