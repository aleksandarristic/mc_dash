
SERVER_IP = "your_server_ip"
SERVER_VERSION = "your_server_version"
SERVER_MOTD = "your_server_motd"
SERVER_PORT = 25565
SERVER_NAME = "your_server_name"
SERVER_MAX_PLAYERS = 20

SECRET_KEY = "your-super-secret-key"
RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = "your_rcon_password"

STATIC = {
    "URL": "/static",
    "DIR": "app/static",
}

TORTOISE_ORM = {
    "connections": {"default": "sqlite://db.sqlite3"},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}

TIMEZONE = "UTC"

try:
    from .settings_local import *  # noqa: F403
except ImportError:
    pass
