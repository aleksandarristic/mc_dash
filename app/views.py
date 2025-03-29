import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.models import ServerSnapshot
import app.config
from app.cache import get_server_status

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def homepage(request: Request):
    # Get live server status from in-memory cache
    status = get_server_status()

    # List available downloads
    download_dir = app.config.DOWNLOADS_DIR
    downloads = [
        f for f in os.listdir(download_dir)
        if os.path.isfile(os.path.join(download_dir, f))
    ] if os.path.exists(download_dir) else []

    # Static server info (config-based)
    server_info = {
        "ip": app.config.SERVER_IP,
        "version": app.config.SERVER_VERSION,
        "motd": app.config.SERVER_MOTD,
    }

    # Last few historical snapshots for context (optional)
    snapshots = await ServerSnapshot.all().order_by("-timestamp").limit(5)

    return templates.TemplateResponse("home.html", {
        "request": request,
        "server_status": status["status"],
        "players_online": status["players_online"],
        "max_players": status["max_players"],
        "online_names": status["player_names"],
        "server_info": server_info,
        "downloads": downloads,
        "snapshots": snapshots
    })
