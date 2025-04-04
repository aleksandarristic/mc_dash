import os

from fastapi import APIRouter, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt

import app.config
from app.auth import admin_required, create_user, login_required
from app.cache import get_server_status
from app.models import ServerSnapshot, User

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["get_user"] = lambda request: getattr(request.state, "user", None)



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
    return templates.TemplateResponse("admin.html", {"request": request})


@router.get("/admin/users")
@admin_required
async def user_list(request: Request, page: int = 1, search: str = ""):
    query = User.all()
    if search:
        query = query.filter(username__icontains=search)

    PAGE_SIZE = 10
    users = (
        await query.order_by("created_at")
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )
    total = await query.count()
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "users": users,
            "search": search,
            "page": page,
            "total_pages": total_pages,
        },
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


@router.post("/admin/delete/{user_id}")
@admin_required
async def delete_user(request: Request, user_id: int):
    user_to_delete = await User.get_or_none(id=user_id)
    if user_to_delete:
        await user_to_delete.delete()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/admin/toggle/{user_id}/{field}")
@admin_required
async def toggle_user_flag(request: Request, user_id: int, field: str):
    user = await User.get_or_none(id=user_id)
    if user and field in {"is_admin", "is_approved"}:
        setattr(user, field, not getattr(user, field))
        await user.save()
    return Response(status_code=204)


@router.get("/admin/create")
@admin_required
async def admin_create_user_form(request: Request):
    return templates.TemplateResponse("admin_create_user.html", {"request": request})


@router.post("/admin/create")
@admin_required
async def admin_create_user_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_approved: bool = Form(False),
    is_admin: bool = Form(False),
):
    existing = await User.get_or_none(username=username)
    if existing:
        return templates.TemplateResponse(
            "admin_create_user.html",
            {"request": request, "error": "Username already exists"},
        )

    hash_pw = bcrypt.hash(password)

    await User.create(
        username=username,
        email=email,
        password_hash=hash_pw,
        is_approved=is_approved,
        is_admin=is_admin,
    )

    return RedirectResponse(
        f"/admin/users?message=User+{username}+created",
        status_code=status.HTTP_302_FOUND,
    )
