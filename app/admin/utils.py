import re
import logging

logger = logging.getLogger(__name__)
pattern = r"There are (\d+) whitelisted player\(s\): (.+)"

def parse_whitelist_response(whitelist_str: str) -> list[str]:
    # Example:
    # "There are 6 whitelisted player(s): Leka, toma, lazar, Andrej_J, geta, Vukvuk"
    match = re.match(pattern, whitelist_str)

    if match:
        count = int(match.group(1))
        players = [p.strip() for p in match.group(2).split(",")]
    else:
        players = []
        count = 0
        logger.warning("No matches while parsing whitelist response")
        logger.debug(f'Whitelist response: {whitelist_str}')

    if len(players) != count:
        raise ValueError(f"Count mismatch: {count} != {len(players)}")

    return players

