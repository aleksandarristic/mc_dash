import asyncio
from datetime import datetime, timedelta
from functools import lru_cache

from mcrcon import MCRcon

from app.config import RCON_HOST, RCON_PASSWORD, RCON_PORT
from app.models import ServerSnapshot

CACHE_TTL_SECONDS = 60
_last_updated = None


@lru_cache(maxsize=1)
def _fetch_server_status():
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command("list")
            parts = response.split(" ")
            players_online = int(parts[2])
            max_players = int(parts[7])

            # Save to DB
            asyncio.create_task(
                ServerSnapshot.create(
                    status="Online",
                    players_online=players_online,
                    max_players=max_players,
                )
            )

            return {
                "status": "Online",
                "players_online": players_online,
                "max_players": max_players,
                "timestamp": datetime.utcnow(),
            }
    except Exception as e:
        print("RCON Error:", e)
        asyncio.create_task(
            ServerSnapshot.create(status="Offline", players_online=0, max_players=0)
        )
        return {
            "status": "Offline",
            "players_online": 0,
            "max_players": 0,
            "timestamp": datetime.utcnow(),
        }


def get_server_status():
    global _last_updated
    if not _last_updated or datetime.utcnow() - _last_updated > timedelta(
        seconds=CACHE_TTL_SECONDS
    ):
        _fetch_server_status.cache_clear()
        _last_updated = datetime.utcnow()
    return _fetch_server_status()
