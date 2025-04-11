import logging
from typing import Dict, List, Optional, Tuple

from mcrcon import MCRcon

from app.models import GamePlayer
from app.settings import RCON_HOST, RCON_PASSWORD, RCON_PORT

logger = logging.getLogger(__name__)


def _send_rcon_command(cmd: str) -> str:
    logger.debug("Sending RCON command: %s", cmd)
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as rcon:
            return rcon.command(cmd)
    except Exception as e:
        logger.error("RCON error: %s", e)
        raise


# 📍 Get player coordinates and dimension
def get_coordinates(
    player_name: str,
) -> Optional[Tuple[str, float, float, float]]:
    # Step 1: Get position
    pos_response = _send_rcon_command(f"data get entity {player_name} Pos")
    try:
        coords_str = pos_response.split("[")[1].split("]")[0]
        x, y, z = [float(c.strip().replace("d", "")) for c in coords_str.split(",")]
    except Exception as e:
        logger.warning("Failed to parse coordinates for %s: %s", player_name, e)
        return None

    # Step 2: Get dimension
    dim_response = _send_rcon_command(f"data get entity {player_name} Dimension")
    try:
        # Should be like: Dimension: "minecraft:overworld"
        dimension = dim_response.split(":", 1)[1].strip().replace('"', "")
    except Exception as e:
        logger.warning("Failed to parse dimension for %s: %s", player_name, e)
        return None

    return dimension, x, y, z


# 🚀 Teleport player to specific coordinates in a dimension
def teleport_to_coords(
    player_name: str,
    x: float,
    y: float,
    z: float,
    dimension: str = "minecraft:overworld",
) -> str:
    cmd = f"/execute in {dimension} run tp {player_name} {x} {y} {z}"
    return _send_rcon_command(cmd)


# 🔁 Teleport player to another player
def teleport_to_player(source_player: str, target_player: str) -> str:
    cmd = f"/tp {source_player} {target_player}"
    return _send_rcon_command(cmd)


async def set_home_from_current_position(playername: str) -> str:
    result = get_coordinates(playername)

    if not result:
        raise Exception("⚠️ Nije moguće dobiti koordinate i dimenziju igrača.")

    dimension, x, y, z = result
    player, _ = await GamePlayer.get_or_create(name=playername)
    player.home_x = x
    player.home_y = y
    player.home_z = z
    player.home_dimension = dimension
    await player.save()
    return f"✅ Kuća je postavljena na ({x:.1f}, {y:.1f}, {z:.1f}) u {dimension}"


async def teleport_home(player_name: str) -> str:
    player = await GamePlayer.get_or_none(name=player_name)
    if not player:
        raise Exception(f'❌ Igrač "{player_name}" nije pronađen!')

    if not player.has_home():
        raise Exception(f'❌ Igrač "{player_name}" postavljene koordinate kuće!')

    logger.debug(
        f"Teleporting {player_name} to home at ({player.home_x}, {player.home_y}, {player.home_z}) in {player.home_dimension}"
    )
    logger.debug(f"Home coords: {player.home_coords()}")

    return teleport_to_coords(
        player_name,
        x=player.home_x,
        y=player.home_y,
        z=player.home_z,
        dimension="minecraft:overworld",
    )


async def get_players_by_names(names: List[str]) -> Dict[str, GamePlayer]:
    """Fetch GamePlayer instances by their names. Returns dict[name] = GamePlayer."""
    players = await GamePlayer.filter(name__in=names)
    return {player.name: player for player in players}
