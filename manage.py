import asyncio
import sys

import uvicorn
from tortoise import Tortoise

from app import models, config
from app.db import generate_schema, init_db


async def get_server_status():
    return await models.ServerSnapshot.first()


async def setup_tortoise_if_needed():
    if not Tortoise._inited:
        await Tortoise.init(
            db_url="sqlite://db.sqlite3", modules={"models": ["app.models"]}
        )


def start_shell(initdb=False):
    import IPython
    import nest_asyncio

    nest_asyncio.apply()  # 🔧 Enable nested loops for await inside shell

    banner = """
🚀 Async Shell (IPython)

Models:
  - ServerSnapshot

Utils:
  - await get_server_status()

🔁 Use 'await' to run async DB queries.
"""

    namespace = {
        "Tortoise": Tortoise,
        "models": models,
        "get_server_status": get_server_status,
        "config": config,
        "asyncio": asyncio,
    }

    async def prepare():
        await setup_tortoise_if_needed()
        if initdb:
            await generate_schema()

    # Run async setup first, outside IPython
    asyncio.run(prepare())

    # Then launch IPython in the current thread, cleanly
    IPython.start_ipython(argv=[], user_ns=namespace, banner1=banner)


# --- Reset DB ---
async def reset_db():
    await setup_tortoise_if_needed()
    print("⚠️  Dropping all tables and reinitializing schema...")
    await Tortoise._drop_databases()
    await generate_schema()
    await Tortoise.close_connections()
    print("✅ Database reset complete.")


# --- Migrate (init schema without drop) ---
async def migrate():
    await setup_tortoise_if_needed()
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()
    print("✅ Schema synchronized (migrated).")


async def init_and_generate():
    print("🔌 Initializing DB...")
    await init_db()
    print("🧱 Generating schema...")
    await generate_schema()
    await Tortoise.close_connections()
    print("✅ Done.")


async def check_models():
    await init_db()
    print("Discovered models:", list(Tortoise.apps.get("models").keys()))


# --- CLI Entry Point ---
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if cmd == "initdb":
        asyncio.run(init_and_generate())

    elif cmd == "shell":
        init_flag = "--initdb" in args
        start_shell(initdb=init_flag)

    elif cmd == "resetdb":
        asyncio.run(reset_db())

    elif cmd == "migrate":
        asyncio.run(migrate())

    elif cmd == "runserver":
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

    elif cmd == "checkmodels":
        asyncio.run(check_models())

    else:
        print("""Usage: manage.py [command]

Commands:
  initdb           Create tables (if not exist)
  migrate          Sync schema without data loss
  resetdb          Drop and recreate all tables
  shell [--initdb] Start interactive IPython shell
  runserver        Run FastAPI app (localhost:8000)
""")
