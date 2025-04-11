import asyncio
import getpass
import subprocess
import sys

import uvicorn
from passlib.hash import bcrypt
from tortoise import Tortoise

from app import settings
from app.db import (
    generate_schema,
    setup_tortoise_if_needed,
    with_db,
)
from app.minecraft.cache import poll_and_cache
from app.models import GamePlayer, ServerSnapshot, User


def aerich_run(*args):
    try:
        subprocess.run(["aerich", *args], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Aerich command failed: {e}")


@with_db
async def get_server_status():
    return await ServerSnapshot.first()


def start_shell(initdb=False):
    import IPython
    import nest_asyncio

    nest_asyncio.apply()

    banner = """
🚀 Async Shell (IPython)

Models:
  - ServerSnapshot
  - User

Utils:
  - await get_server_status()
"""

    namespace = {
        "Tortoise": Tortoise,
        "get_server_status": get_server_status,
        "config": settings,
        "asyncio": asyncio,
        "User": User,
        "GamePlayer": GamePlayer,
        "ServerSnapshot": ServerSnapshot,
    }

    async def prepare():
        await setup_tortoise_if_needed()
        if initdb:
            await generate_schema()

    asyncio.run(prepare())
    IPython.start_ipython(argv=[], user_ns=namespace, banner1=banner)


@with_db
async def check_models():
    print("Discovered models:", list(Tortoise.apps.get("models").keys()))


@with_db
async def fetch_status():
    await setup_tortoise_if_needed()
    await poll_and_cache()
    print("✅ Status snapshot saved.")


# --- Show GamePlayer last seen info ---
@with_db
async def show_recent_players():
    players = await GamePlayer.all().order_by("-last_seen").limit(20)

    print("📋 Recently Seen Game Players:")
    print("-" * 60)
    for p in players:
        last_seen = (
            p.last_seen.strftime("%Y-%m-%d %H:%M:%S") if p.last_seen else "Never"
        )
        coords = (
            f"({p.last_seen_x:.1f}, {p.last_seen_y:.1f}, {p.last_seen_z:.1f})"
            if p.last_seen_x is not None
            else "—"
        )
        print(f"{p.name:20} | Last seen: {last_seen} | Coords: {coords}")


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
    game_name = input("Game Name: ")
    hash_pw = bcrypt.hash(password)

    existing_user = await User.get_or_none(username=username)
    if existing_user:
        print("User already exists!")
        return

    await User.create(
        username=username,
        game_name=game_name,
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


@with_db
async def reset_password(username):
    user = await User.get_or_none(username=username)
    if not user:
        print("❌ User not found")
    else:
        new_password = getpass.getpass("New Password: ")
        user.set_password(new_password)
        await user.save()
        print(f"✅ Password for '{username}' reset.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    args = sys.argv[2:]

    if cmd == "initdb":
        aerich_run("init-db")

    elif cmd == "migrate":
        name = None
        if "--name" in args:
            idx = args.index("--name")
            if idx + 1 < len(args):
                name = args[idx + 1]
                aerich_run("migrate", "--name", name)
            else:
                print("⚠️  --name requires a value.")
                sys.exit(1)
        else:
            aerich_run("migrate")
        aerich_run("upgrade")

    elif cmd == "upgrade":
        aerich_run("upgrade")

    elif cmd == "resetdb":
        import os

        db_file = "db.sqlite3"
        if os.path.exists(db_file):
            os.remove(db_file)
            print("🗑️ Deleted database.")
        else:
            print("ℹ️ No database file found.")

        migrations_dir = "migrations/models"
        for f in os.listdir(migrations_dir):
            if f.endswith(".py") and f != "__init__.py":
                os.remove(os.path.join(migrations_dir, f))
                print(f"✂️ Removed migration: {f}")

        aerich_run("init-db")

    elif cmd == "checkmodels":
        asyncio.run(check_models())

    elif cmd == "fetchstatus":
        asyncio.run(fetch_status())

    elif cmd == "createsuperuser":
        asyncio.run(create_admin())

    elif cmd == "createuser":
        asyncio.run(create_user())

    elif cmd == "resetpassword":
        username = args[0] if args else None
        if not username:
            print("Usage: manage.py resetpassword <username>")
        else:
            asyncio.run(reset_password(username=username))

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

    elif cmd == "shell":
        init_flag = "--initdb" in args
        start_shell(initdb=init_flag)

    elif cmd == "runserver":
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

    elif cmd == "recentplayers":
        asyncio.run(show_recent_players())

    else:
        print("""Usage: manage.py [command]

Commands:
    initdb              Run Aerich init-db
    migrate [--name]    Create & apply migrations (optional name)
    upgrade             Apply unapplied migrations
    resetdb             Drop DB & reinit using Aerich
    checkmodels         Print discovered models

    createsuperuser     Create an admin user
    createuser          Create a regular user
    resetpassword       Reset user password
    promote             Promote user to admin
    activate            Activate user account
    deactivate          Deactivate user account
    deleteuser          Delete user account

    fetchstatus         Poll and save server status
    recentplayers       Show recently seen Game Players
    shell [--initdb]    Async IPython shell
    runserver           Run FastAPI app
""")
