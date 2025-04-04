import asyncio
import getpass
import sys

import uvicorn
from passlib.hash import bcrypt
from tortoise import Tortoise

from app import config
from app.models import User, ServerSnapshot
from app.cache import poll_and_cache
from app.db import generate_schema, init_db, setup_tortoise_if_needed, with_db


async def get_server_status():
    return await ServerSnapshot.first()


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
        "get_server_status": get_server_status,
        "config": config,
        "asyncio": asyncio,
        "User": User,
        "ServerSnapshot": ServerSnapshot,
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


async def fetch_status():
    await setup_tortoise_if_needed()
    await poll_and_cache()
    print("✅ Status snapshot saved.")


@with_db
async def create_admin():
    username = input("Username: ")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    hash_pw = bcrypt.hash(password)

    existing_user = await User.get_or_none(username=username)
    if existing_user:
        print("User already exists!")
        return

    await User.create(
        username=username,
        email=email,
        password_hash=hash_pw,
        is_admin=True,
        is_approved=True,
    )
    print(f"✅ Admin user '{username}' created.")


@with_db
async def create_user():
    username = input("Username: ")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    hash_pw = bcrypt.hash(password)

    existing_user = await User.get_or_none(username=username)
    if existing_user:
        print("User already exists!")
        return

    await User.create(
        username=username,
        email=email,
        password_hash=hash_pw,
        is_admin=False,
        is_approved=False,
    )
    print(f"✅ User '{username}' created.")


@with_db
async def promote_user(username):
    user = await User.get_or_none(username=username)
    if not user:
        print("❌ User not found")
    else:
        user.is_admin = True
        user.is_approved = True
        await user.save()
        print(f"✅ User '{username}' promoted to admin.")


@with_db
async def activate_user(username):
    user = await User.get_or_none(username=username)
    if not user:
        print("❌ User not found")
    else:
        user.is_approved = True
        await user.save()
        print(f"✅ User '{username}' activated.")


@with_db
async def deactivate_user(username):
    user = await User.get_or_none(username=username)
    if not user:
        print("❌ User not found")
    else:
        user.is_approved = False
        await user.save()
        print(f"✅ User '{username}' deactivated.")


@with_db
async def delete_user(username):
    user = await User.get_or_none(username=username)
    if not user:
        print("❌ User not found")
    else:
        await user.delete()
        print(f"✅ User '{username}' deleted.")


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

    elif cmd == "fetchstatus":
        asyncio.run(fetch_status())

    elif cmd == "checkmodels":
        asyncio.run(check_models())

    ### USER MANAGEMENT COMMANDS
    elif cmd == "createsuperuser":
        asyncio.run(create_admin())

    elif cmd == "createuser":
        asyncio.run(create_user())

    elif cmd == "promote":
        username = args[0] if args else None
        if not username:
            print("Usage: manage.py promote <username>")
        else:
            asyncio.run(promote_user(username=username))

    elif cmd == "activate":
        username = args[0] if args else None
        if not username:
            print("Usage: manage.py activate <username>")
        else:
            asyncio.run(activate_user(username=username))

    elif cmd == "deactivate":
        username = args[0] if args else None
        if not username:
            print("Usage: manage.py deactivate <username>")
        else:
            asyncio.run(deactivate_user(username=username))

    else:
        print("""Usage: manage.py [command]

Commands:
    shell [--initdb] Start interactive IPython shell

    initdb              Create tables (if not exist)
    migrate             Sync schema without data loss
    resetdb             Drop and recreate all tables
    checkmodels         Print discovered models
              
    createsuperuser     Create an admin user
    createuser          Create a regular user
    promote             Promote user to admin
    activate            Activate user account
    deactivate          Deactivate user account
    deleteuser          Delete user account
    
              
    fetchstatus         Fetch and save server status
              
    runserver           Run FastAPI app (localhost:8000)
""")
