import logging
import re
from typing import Dict, List, Tuple

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
        logger.debug(f"Whitelist response: {whitelist_str}")

    if len(players) != count:
        raise ValueError(f"Count mismatch: {count} != {len(players)}")

    return players


def parse_banlist_response(text: str) -> Tuple[int, Dict[str, List[Dict[str, str]]]]:
    # Extract number of bans
    count_match = re.search(r"There are (\d+) ban\(s\):", text)
    ban_count = int(count_match.group(1)) if count_match else 0

    # Pattern to extract each ban entry
    ban_pattern = re.compile(
        r"^(?P<identifier>\S+)\s+was banned by (?P<banned_by>[^:]+):\s+(?P<ban_message>.+)$",
        re.MULTILINE
    )

    details = {
        "users": [],
        "uuids": [],
        "ips": []
    }

    for match in ban_pattern.finditer(text):
        identifier = match.group("identifier")
        banned_by = match.group("banned_by").strip()
        ban_message = match.group("ban_message").strip()

        entry = {
            "identifier": identifier,
            "banned_by": banned_by,
            "message": ban_message
        }

        if re.match(r"\d{1,3}(?:\.\d{1,3}){3}$", identifier):
            details["ips"].append(entry)
        elif re.match(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", identifier):
            details["uuids"].append(entry)
        else:
            details["users"].append(entry)

    return ban_count, details
