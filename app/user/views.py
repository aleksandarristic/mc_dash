from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.user.auth import create_user, login_required
from app.models import GamePlayer, User
from app.utils import flash, render_template

router = APIRouter()  # admin app router
templates = Jinja2Templates(directory="app/templates")  # admin app templates


@router.get("/register", name="user_register")
async def register_form(request: Request):
    return render_template("user/register.html", request, {})


@router.post("/register", name="user_register_post")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    existing_user = await User.get_or_none(username=username)
    if existing_user:
        return render_template(
            "user/register.html", request, {"error": "Username already exists"}
        )

    await create_user(username, email, password)
    return render_template(
        "user/login.html", request, {"message": "User registered successfully!"}
    )


@router.get("/login", name="user_login")
async def login_form(request: Request):
    return render_template("user/login.html", request, {})


@router.post("/login", name="user_login_post")
async def login_user(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    user = await User.get_or_none(username=username)
    if not user or not user.verify_password(password):
        return render_template(
            "user/login.html", request, {"error": "Invalid credentials"}
        )
    if not user.is_approved:
        return render_template(
            "user/login.html", request, {"error": "User not approved"}
        )

    # log the user in
    request.session["user_id"] = user.id

    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)


@router.get("/logout", name="user_logout")
@login_required
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

@router.get("/profile", name="user_profile")
@login_required
async def profile_view(request: Request):
    await request.state.user.fetch_related("game_player")
    game_players = await GamePlayer.all().order_by("name")
    return render_template("user/profile.html", request, {
        "game_players": game_players
    })

@router.post("/profile", name="user_profile_update")
@login_required
async def update_profile(request: Request):
    form = await request.form()
    game_player_id = form.get("game_player_id") or None

    user = request.state.user

    if game_player_id:
        player = await GamePlayer.get_or_none(id=int(game_player_id))
        user.game_player = player
    else:
        user.game_player = None

    await user.save()
    return RedirectResponse(url=request.url_for("user_profile"), status_code=302)

@router.post("/change-password", name="user_change_password")
@login_required
async def change_password(request: Request, password: str = Form(...), confirm_password: str = Form(...)):
    user = request.state.user

    if password != confirm_password:
        flash(request, "Lozinke se ne poklapaju.", "danger")
        return RedirectResponse(request.url_for("user_profile"), status_code=302)

    # You can improve complexity rules here
    # if len(password) < 8:
    #     flash(request, "Lozinka mora imati bar 8 karaktera.", "danger")
    #     return RedirectResponse(request.url_for("user_profile"), status_code=302)

    await user.set_password(password)
    flash(request, "Lozinka uspešno promenjena!", "success")
    return RedirectResponse(request.url_for("user_profile"), status_code=302)
