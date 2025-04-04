from functools import wraps

from tortoise import Tortoise


async def init_db():
    if not Tortoise._inited:
        await Tortoise.init(
            db_url="sqlite://db.sqlite3", modules={"models": ["app.models"]}
        )


async def generate_schema():
    await Tortoise.generate_schemas(safe=False)


def with_db(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        await init_db()
        try:
            return await func(*args, **kwargs)
        finally:
            await Tortoise.close_connections()

    return wrapper


async def setup_tortoise_if_needed():
    if not Tortoise._inited:
        await Tortoise.init(
            db_url="sqlite://db.sqlite3", modules={"models": ["app.models"]}
        )
