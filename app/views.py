import logging

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

import app.settings
from app.user.auth import login_required
from app.minecraft.cache import get_server_status
from app.models import GamePlayer, ServerSnapshot
from app.utils import render_template

logger = logging.getLogger(__name__)
router = APIRouter()  # main app router
templates = Jinja2Templates(directory="app/templates")  # main app templates


@router.get("/", name="homepage")
@login_required
async def homepage(request: Request):
    logger.debug("Homepage accessed")

    # Get live server status from in-memory cache
    status = get_server_status()
    # mock status for testing
    # status = {
    #     "status": "Online",
    #     "players_online": 1,
    #     "max_players": 20,
    #     "player_names": ["leka"],
    #     "timestamp": datetime.utcnow(),
    # }
    

    # Static server info (config-based)
    server_info = {
        "ip": app.settings.SERVER_IP,
        "version": app.settings.SERVER_VERSION,
        "motd": app.settings.SERVER_MOTD,
    }

    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Query players seen today
    players_today = await GamePlayer.filter(last_seen__gte=start_of_day).order_by(
        "last_seen"
    )

    player_info_map = {player.name: player for player in players_today}

    snapshots = await ServerSnapshot.all().order_by("-timestamp").limit(1)

    context = {
        "server_status": status["status"],
        "players_online": status["players_online"],
        "max_players": status["max_players"],
        "online_names": status["player_names"],
        "server_info": server_info,
        "snapshots": snapshots,
        "players_today": players_today,
        "player_info_map": player_info_map,
    }
    logger.debug(f"Context for homepage: {context}")

    return render_template(
        "home.html",
        request,
        context,
    )
