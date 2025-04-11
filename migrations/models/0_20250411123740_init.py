from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "gameplayer" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(32) NOT NULL UNIQUE,
    "home_x" REAL,
    "home_y" REAL,
    "home_z" REAL,
    "home_dimension" VARCHAR(64),
    "last_seen" TIMESTAMP,
    "last_seen_x" REAL,
    "last_seen_y" REAL,
    "last_seen_z" REAL,
    "last_seen_dimension" VARCHAR(64)
);
CREATE TABLE IF NOT EXISTS "serversnapshot" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "timestamp" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(10) NOT NULL,
    "players_online" INT NOT NULL,
    "max_players" INT NOT NULL,
    "player_names" JSON
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(150) NOT NULL UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "is_admin" INT NOT NULL DEFAULT 0,
    "is_approved" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "game_player_id" INT REFERENCES "gameplayer" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
