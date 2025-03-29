from tortoise import fields, models

class ServerSnapshot(models.Model):
    id = fields.IntField(pk=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    status = fields.CharField(max_length=10)
    players_online = fields.IntField()
    max_players = fields.IntField()
    player_names = fields.JSONField(null=True)
