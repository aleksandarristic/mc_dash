import logging
from zoneinfo import ZoneInfo

from passlib.hash import bcrypt
from tortoise import fields, models

logger = logging.getLogger(__name__)


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=150, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)

    is_admin = fields.BooleanField(default=False)
    is_approved = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    # Optional link to one in-game character
    game_player: fields.ForeignKeyNullableRelation["GamePlayer"] = (
        fields.ForeignKeyField(
            "models.GamePlayer", null=True, related_name="linked_users"
        )
    )

    def verify_password(self, raw_password: str) -> bool:
        return bcrypt.verify(raw_password, self.password_hash)

    async def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hash(raw_password)
        await self.save()

    def __str__(self):
        return self.username

    def __repr__(self):
        return f"<User: {self.username} (ID: {self.id})>"


class GamePlayer(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32, unique=True)

    # Home coordinates and dimension
    home_x = fields.FloatField(null=True)
    home_y = fields.FloatField(null=True)
    home_z = fields.FloatField(null=True)
    home_dimension = fields.CharField(max_length=64, null=True)

    # Last seen data
    last_seen = fields.DatetimeField(null=True)
    last_seen_x = fields.FloatField(null=True)
    last_seen_y = fields.FloatField(null=True)
    last_seen_z = fields.FloatField(null=True)
    last_seen_dimension = fields.CharField(max_length=64, null=True)

    @staticmethod
    def _friendly_dimension_name(dim: str) -> str:
        mapping = {
            "minecraft:overworld": "overworld",
            "minecraft:the_nether": "nether",
            "minecraft:the_end": "end",
        }
        return mapping.get(dim, dim or "-")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<GamePlayer: {self.name} (ID: {self.id})>"

    def href(self):
        return f"/players/{self.id}/"

    def has_home(self):
        has_home = (
            self.home_x is not None
            and self.home_y is not None
            and self.home_z is not None
        )
        logger.debug(f"Player {self.name} has home: {has_home}")
        return has_home

    def home_coords(self):
        if (
            self.home_x is not None
            and self.home_y is not None
            and self.home_z is not None
        ):
            dim = self._friendly_dimension_name(self.home_dimension)
            return f"({self.home_x:.1f}, {self.home_y:.1f}, {self.home_z:.1f}) u {dim}"
        return "—"

    def last_seen_coords(self, rich=True):
        if (
            self.last_seen_x is not None
            and self.last_seen_y is not None
            and self.last_seen_z is not None
        ):
            if rich:
                dim = self._friendly_dimension_name(self.last_seen_dimension)
                return f"({self.last_seen_x:.1f}, {self.last_seen_y:.1f}, {self.last_seen_z:.1f}) u {dim}"
            else:
                return f"({self.last_seen_x:.1f}, {self.last_seen_y:.1f}, {self.last_seen_z:.1f})"
        return "—"

    def last_seen_time(self, format: str = "%Y-%m-%d %H:%M:%S", default: str = "Nikad"):
        if self.last_seen is not None:
            return self.last_seen.astimezone(ZoneInfo("Europe/Belgrade")).strftime(
                format
            )
        return default


class ServerSnapshot(models.Model):
    id = fields.IntField(pk=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=10)
    players_online = fields.IntField()
    max_players = fields.IntField()
    player_names = fields.JSONField(null=True)

    def __str__(self):
        return f"Snapshot at {self.timestamp} - {self.status} ({self.players_online}/{self.max_players})"

    def __repr__(self):
        return f"<ServerSnapshot: {self.timestamp} ({self.players_online}/{self.max_players})>"
