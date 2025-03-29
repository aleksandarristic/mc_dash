import asyncio
from datetime import datetime
from mcrcon import MCRcon

from app.config import RCON_HOST, RCON_PASSWORD, RCON_PORT
from app.models import ServerSnapshot

# In-memory cache for live status
_server_status_cache = {
    "status": "Unknown",
    "players_online": 0,
    "max_players": 0,
    "player_names": [],
    "timestamp": datetime.utcnow(),
}

def get_server_status():
    """Returns the most recent cached server status."""
    return _server_status_cache

async def poll_server_status_loop(interval_seconds: int = 60):
    """Background polling loop that updates server status and stores snapshots."""
    while True:
        await poll_and_cache()
        await asyncio.sleep(interval_seconds)

async def poll_and_cache():
    """Fetch status via RCON, update cache, and store to DB."""
    global _server_status_cache

    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command("list")
            # Example response:
            # "There are 2 of a max of 20 players online: Player1, Player2"
            parts = response.split(" ")
            players_online = int(parts[2])
            max_players = int(parts[7])

            # Extract player names if available
            if ":" in response:
                player_str = response.split(":", 1)[1].strip()
                player_names = [name.strip() for name in player_str.split(",") if name.strip()]
            else:
                player_names = []

            status_data = {
                "status": "Online",
                "players_online": players_online,
                "max_players": max_players,
                "player_names": player_names,
                "timestamp": datetime.utcnow(),
            }

    except Exception as e:
        print("RCON error:", e)
        status_data = {
            "status": "Offline",
            "players_online": 0,
            "max_players": 0,
            "player_names": [],
            "timestamp": datetime.utcnow(),
        }

    # Update in-memory cache
    _server_status_cache.update(status_data)

    # Persist to DB
    await ServerSnapshot.create(
        status=status_data["status"],
        players_online=status_data["players_online"],
        max_players=status_data["max_players"],
        player_names=status_data["player_names"]
    )
