from tortoise import fields, models
from passlib.hash import bcrypt


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=150, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    is_admin = fields.BooleanField(default=False)
    is_approved = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    def verify_password(self, raw_password: str) -> bool:
        return bcrypt.verify(raw_password, self.password_hash)
    
    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hash(raw_password)
        self.save()


class ServerSnapshot(models.Model):
    id = fields.IntField(pk=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=10)
    players_online = fields.IntField()
    max_players = fields.IntField()
    player_names = fields.JSONField(null=True)
