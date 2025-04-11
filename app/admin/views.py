from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from starlette import status

from app.models import GamePlayer, User
from app.user.auth import admin_required
from app.utils import flash, redirect_back, render_template

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", name="admin_dashboard")
@admin_required
async def admin_dashboard(request: Request):
    return render_template("admin/admin.html", request, {})


@router.get("/users", name="admin_user_list")
@admin_required
async def user_list(request: Request, page: int = 1, search: str = ""):
    query = User.all().prefetch_related("game_player")
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

    game_players = await GamePlayer.all().order_by("name")

    return render_template(
        "admin/admin_users.html",
        request,
        {
            "users": users,
            "search": search,
            "page": page,
            "total_pages": total_pages,
            "all_game_players": game_players,
        },
    )


@router.post("/approve/{user_id}", name="admin_approve_user")
@admin_required
async def approve_user(request: Request, user_id: int):
    user = await User.get_or_none(id=user_id)
    if user:
        user.is_approved = True
        await user.save()
    users_url = request.url_for("admin_user_list")
    flash(
        request,
        f'Korisnik "{user.username}" odobren.',
        "success",
    )
    return RedirectResponse(users_url, status_code=302)


@router.post("/promote/{user_id}", name="admin_promote_user")
@admin_required
async def promote_user(request: Request, user_id: int):
    user = await User.get_or_none(id=user_id)
    if user:
        user.is_admin = True
        await user.save()
    users_url = request.url_for("admin_user_list")
    flash(
        request,
        f'Korisnik "{user.username}" postavljen kao admin.',
        "success",
    )
    return RedirectResponse(users_url, status_code=302)


@router.post("/delete/{user_id}", name="admin_delete_user")
@admin_required
async def delete_user(request: Request, user_id: int):
    user_to_delete = await User.get_or_none(id=user_id)
    if user_to_delete:
        await user_to_delete.delete()
    users_url = request.url_for("admin_user_list")
    flash(
        request,
        f'Korisnik "{user_to_delete.username}" obrisan.',
        "success",
    )
    return RedirectResponse(users_url, status_code=302)


@router.post("/toggle/{user_id}/{field}", name="admin_toggle_user_flag")
@admin_required
async def toggle_user_flag(request: Request, user_id: int, field: str):
    user = await User.get_or_none(id=user_id)
    if user and field in {"is_admin", "is_approved"}:
        setattr(user, field, not getattr(user, field))
        await user.save()
    flash(request, f'Korisnik "{user.username}" ažuriran.', "success")
    return Response(status_code=204)


@router.get("/create", name="admin_create_user")
@admin_required
async def admin_create_user_form(request: Request):
    return render_template("admin/admin_create_user.html", request, {})


@router.post("/create", name="admin_create_user_submit")
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
        flash(request, f'Greška! Korisničko ime "{username}" već postoji!', "error")
        return RedirectResponse(
            request.url_for("admin_create_user"),
            status_code=status.HTTP_302_FOUND,
        )

    hash_pw = bcrypt.hash(password)

    await User.create(
        username=username,
        email=email,
        password_hash=hash_pw,
        is_approved=is_approved,
        is_admin=is_admin,
    )

    flash(request, f'Korisnik "{username}" kreiran!', "success")
    return RedirectResponse(
        request.url_for("admin_user_list"),
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/update-user-game-player/{user_id}", name="update_user_game_player")
@admin_required
async def update_user_game_player(request: Request, user_id: int):
    form = await request.form()
    game_player_id = form.get("game_player_id") or None

    user = await User.get_or_none(id=user_id)
    if not user:
        flash(request, f"Korisnik ID={user_id} ne postoji!", "error")
        return RedirectResponse(
            url=request.url_for("admin_user_list"), status_code=status.HTTP_302_FOUND
        )

    if game_player_id:
        player = await GamePlayer.get_or_none(id=int(game_player_id))
        user.game_player = player
    else:
        user.game_player = None

    await user.save()
    flash(request, f'Korisnik "{user}" ažuriran!', "success")
    return RedirectResponse(
        url=request.url_for("admin_user_list"), status_code=status.HTTP_302_FOUND
    )


@router.get("/gameplayers", name="admin_gameplayer_list")
@admin_required
async def gameplayer_list(request: Request):
    players = await GamePlayer.all().prefetch_related("linked_users")
    return render_template(
        "admin/admin_gameplayers.html", request, {"players": players}
    )


@router.get("/gameplayers/create", name="admin_create_gameplayer_form")
@admin_required
async def create_gameplayer_form(request: Request):
    return render_template("admin/admin_create_gameplayer.html", request, {})


@router.post("/gameplayers/create", name="admin_create_gameplayer")
@admin_required
async def create_gameplayer(request: Request, name: str = Form(...)):
    existing = await GamePlayer.get_or_none(name=name)

    if existing:
        flash(request, f"Greška! Igrač sa imenom '{name}' već postoji!", "error")
        return RedirectResponse(
            request.url_for("admin_create_gameplayer_form"),
            status_code=status.HTTP_302_FOUND,
        )

    await GamePlayer.create(name=name)
    flash(request, f"Igrač {name} kreiran", "success")
    return RedirectResponse(
        request.url_for("admin_gameplayer_list"), status_code=status.HTTP_302_FOUND
    )


@router.post("/gameplayers/delete/{player_id}", name="admin_delete_gameplayer")
@admin_required
async def delete_gameplayer(request: Request, player_id: int):
    player = await GamePlayer.get_or_none(id=player_id)
    if player:
        await player.delete()
        flash(request, f"Igrač {player.name} obrisan", "success")
    else:
        flash(request, f"Igrač {player_id} ne postoji ili je već obrisan", "error")

    return RedirectResponse(
        request.url_for("admin_gameplayer_list"), status_code=status.HTTP_302_FOUND
    )


@router.post("/gameplayers/update-coords/{player_id}", name="admin_update_coords")
@admin_required
async def update_coords(
    request: Request,
    player_id: int,
    home_x: float = Form(...),
    home_y: float = Form(...),
    home_z: float = Form(...),
    home_dimension: Optional[str] = Form(None),
):
    player = await GamePlayer.get_or_none(id=player_id)
    if player:
        player.home_x = home_x
        player.home_y = home_y
        player.home_z = home_z
        if home_dimension:
            player.home_dimension = home_dimension
        await player.save()
    flash(request, f'Nove koordinate za igrača "{player}" sačuvane.', "success")
    return redirect_back(request, request.url_for("admin_gameplayer_list"))


@router.get("/gameplayers/{player_id}", name="admin_gameplayer_detail")
@admin_required
async def gameplayer_detail(request: Request, player_id: int):
    player = await GamePlayer.get_or_none(id=player_id).prefetch_related("linked_users")
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return render_template("admin/gameplayer_detail.html", request, {"player": player})
