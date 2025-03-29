from tortoise import Tortoise

async def init_db():
    if not Tortoise._inited:
        await Tortoise.init(
            db_url='sqlite://db.sqlite3',
            modules={'models': ['app.models']}
        )

async def generate_schema():
    await Tortoise.generate_schemas(safe=False)
