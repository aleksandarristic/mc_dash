import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.minecraft.mc_utils import get_coordinates, set_home_from_current_position, teleport_home, teleport_to_coords
from app.models import GamePlayer
from app.user.auth import admin_required, login_required
from app.utils import render_template

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/teleport", name="minecraft_teleport_form")
@login_required
async def teleport_form(request: Request):
    return render_template("minecraft/teleport.html", request, {})


@router.get("/location", name="minecraft_player_location")
@login_required
async def player_location(request: Request):
    user = request.state.user
    coords = await get_coordinates(user.username)

    render_template(
        "minecraft/teleport.html",
        request,
        {
            "message": coords,
            "username": user.username,
            "x": coords.split(" ")[0],
            "y": coords.split(" ")[1],
            "z": coords.split(" ")[2],
        },
    )


@router.post("/set-home", name="minecraft_set_home")
@login_required
async def set_player_home(request: Request):
    user = request.state.user
    game_player = await GamePlayer.get_or_none(linked_users__id=user.id)
    if not game_player:
        return JSONResponse({"success": False, "message": f'Greška! Nema povezanog igrača za korisnika "{user.username}"!'})

    try:
        result = await set_home_from_current_position(game_player.name)
        response = {"success": True, "message": result}
    except Exception as e:
        response = {"success": False, "message": str(e)}
    return JSONResponse(response)


@router.post("/teleport-home", name="minecraft_teleport_home")
@login_required
async def teleport_player_home(request: Request):
    user = request.state.user
    logger.debug(f"Teleporting {user.username} to home")
    # Check if the user has a linked GamePlayer
    game_player = await GamePlayer.get_or_none(linked_users__id=user.id)
    if not game_player:
        return JSONResponse({"success": False, "message": f'Greška! Nema povezanog igrača za korisnika "{user.username}"!'})
    
    try:
        result = await teleport_home(game_player.name)
        logger.debug(f"Teleport result: \"{result}\"")
        if "No entity was found" in result:
            return JSONResponse({"success": False, "message": f'Greška! Da li je "{game_player.name}" online?'})
        response = {"success": True, "message": result}
    except Exception as e:
        response = {"success": False, "message": f"{e}"}

    return JSONResponse(response)


@router.post("/teleport-coords", name="minecraft_teleport_coords")
@login_required
async def teleport_to_custom_coords(
    request: Request,
    x: float = Form(...),
    y: float = Form(...),
    z: float = Form(...),
    dimension: str = Form("minecraft:overworld"),
):
    user = request.state.user
    result = await teleport_to_coords(user.username, x, y, z, dimension)
    return JSONResponse({"success": True, "message": result})


@router.post("/admin/teleport", name="minecraft_admin_teleport_player")
@admin_required
async def admin_teleport_player(
    request: Request,
    playername: str = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    z: float = Form(...),
):
    result = await teleport_to_coords(playername, x, y, z)
    return render_template("minecraft/teleport.html", request, {"message": result})


@router.get("/gameplayers/{player_id}", name="admin_gameplayer_detail")
@login_required
async def gameplayer_detail(request: Request, player_id: int):
    player = await GamePlayer.get_or_none(id=player_id).prefetch_related("linked_users")
    if not player:
        pass  # redirect to your own profile
        # return RedirectResponse(request.url_for("admin_gameplayer_list"), status_code=302)
    return render_template("admin/gameplayer_detail.html", request, {"player": player})
