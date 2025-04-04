import os

RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = "your_rcon_password"

SERVER_IP = "your_server_ip"
SERVER_VERSION = "your_server_version"
SERVER_MOTD = "your_server_motd"

DOWNLOADS_DIR = "app/static/downloads"  # Directory for downloads

SECRET_KEY = "your-super-secret-key"

STATIC = {
    "URL": "/static",
    "DIR": "app/static",
}

try:
    from .config_local import *  # noqa: F403
except ImportError:
    pass

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)
