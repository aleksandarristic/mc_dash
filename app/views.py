from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime, timedelta
from app.models import ServerSnapshot
from app.cache import get_server_status
import app.config

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def homepage(request: Request):
    status = get_server_status()

    download_dir = app.config.DOWNLOADS_DIR
    downloads = [
        f for f in os.listdir(download_dir)
        if os.path.isfile(os.path.join(download_dir, f))
    ] if os.path.exists(download_dir) else []

    server_info = {
        "ip": app.config.SERVER_IP,
        "version": app.config.SERVER_VERSION,
        "motd": app.config.SERVER_MOTD,
    }

    return templates.TemplateResponse("home.html", {
        "request": request,
        "server_status": status["status"],
        "players_online": status["players_online"],
        "max_players": status["max_players"],
        "server_info": server_info,
        "downloads": downloads
    })

@router.get("/history")
async def history(request: Request, range: str = Query("1h")):
    now = datetime.utcnow()
    range_map = {
        "1h": now - timedelta(hours=1),
        "6h": now - timedelta(hours=6),
        "12h": now - timedelta(hours=12),
        "24h": now - timedelta(hours=24),
        "7d": now - timedelta(days=7),
    }
    start_time = range_map.get(range, range_map["1h"])

    snapshots = await ServerSnapshot.filter(timestamp__gte=start_time).order_by("timestamp")
    labels = [snap.timestamp.strftime("%H:%M") for snap in snapshots]
    values = [snap.players_online for snap in snapshots]

    return templates.TemplateResponse("history.html", {
        "request": request,
        "labels": labels,
        "values": values,
        "range": range
    })
