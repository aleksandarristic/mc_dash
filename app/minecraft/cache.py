import asyncio
import logging
from datetime import datetime

from mcrcon import MCRcon

from app.models import GamePlayer, ServerSnapshot, User
from app.settings import RCON_HOST, RCON_PASSWORD, RCON_PORT

logger = logging.getLogger(__name__)

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
    global _server_status_cache

    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as rcon:
            response = rcon.command("list")

            # Defensive parsing
            if not response or "players online" not in response:
                raise ValueError(f"[RCON] Unexpected response format: {response}")

            # Try to extract counts safely
            try:
                parts = response.split()
                players_online = int(parts[2])
                max_players = int(parts[7])
            except (IndexError, ValueError) as e:
                raise ValueError(
                    f"[Parse error] Failed to parse player counts: {response}"
                ) from e

            # Extract player names
            if ":" in response:
                player_str = response.split(":", 1)[1].strip()
                player_names = [
                    name.strip() for name in player_str.split(",") if name.strip()
                ]
            else:
                player_names = []

            # ✅ Ensure all players exist as GamePlayer
            for name in player_names:
                player, created = await GamePlayer.get_or_create(name=name)

                # Link user if needed
                if created:
                    logger.debug(f"New player created: {name}")
                    matching_user = await User.get_or_none(
                        game_player=None, game_name=name
                    )
                    if matching_user:
                        matching_user.game_player = player
                        await matching_user.save()
                else:
                    logger.debug(f"Player found: {name}")

                # ⏱️ Update last_seen timestamp
                player.last_seen = datetime.utcnow()
                logger.debug(f"Player {name} last seen updated.")

                # 📍 Try to get position
                try:
                    pos_response = rcon.command(f"data get entity {name} Pos")
                    # Example: 'Pos: [123.0d, 64.0d, -321.5d]'
                    coords = pos_response.split("[")[1].split("]")[0].split(",")
                    x, y, z = [float(c.strip().replace("d", "")) for c in coords]
                    player.last_seen_x, player.last_seen_y, player.last_seen_z = x, y, z
                    logger.debug(
                        f"Player {name} last seen at coordinates: ({x}, {y}, {z})"
                    )
                except Exception as e:
                    logger.warning(f"Failed to get position for {name}: {e}")


                # 📍 Try to get dimension
                try:
                    dim_response = rcon.command(f"data get entity {name} Dimension")
                    logger.debug(f"Dimension response for {name}: {dim_response}")
                    # Example: 'Vukvuk has the following entity data: "minecraft:overworld"'
                    if "minecraft:" not in dim_response:
                        raise ValueError(f"Invalid dimension format: {dim_response}")
                    dimension = dim_response.split("\"")[1].strip().replace('"', "")
                    logger.debug(
                        f"Parsed dimension for {name}: {dimension}"
                    )
                    player.last_seen_dimension = dimension
                    logger.debug(f"Player {name} is in dimension: {dimension}")
                except Exception as e:
                    logger.warning(f"Failed to get dimension for {name}: {e}")

                await player.save()
                logger.debug(f"Player {name} saved to DB.")

            status_data = {
                "status": "Online",
                "players_online": players_online,
                "max_players": max_players,
                "player_names": player_names,
                "timestamp": datetime.utcnow(),
            }

    except Exception as e:
        logger.error(f"[RCON GREŠKA]: {e}")
        status_data = {
            "status": "Offline",
            "players_online": 0,
            "max_players": 0,
            "player_names": [],
            "timestamp": datetime.utcnow(),
        }

    _server_status_cache.update(status_data)

    # 💾 Store in DB
    await ServerSnapshot.create(
        status=status_data["status"],
        players_online=status_data["players_online"],
        max_players=status_data["max_players"],
        player_names=status_data["player_names"],
    )

    # 🧹 Keep only the latest 20 entries
    snapshots = await ServerSnapshot.all().order_by("-timestamp")
    if len(snapshots) > 20:
        for old in snapshots[20:]:
            await old.delete()
