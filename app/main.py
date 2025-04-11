import asyncio
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from tortoise.contrib.fastapi import register_tortoise

from app import settings
from app.admin import admin_routes
from app.configure_logging import configure_logging
from app.minecraft import minecraft_routes
from app.minecraft.cache import poll_server_status_loop
from app.user import user_routes
from app.views import router

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

# 🔐 Add session middleware (required for login sessions)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Static files (e.g., downloads)
app.mount(
    settings.STATIC["URL"], StaticFiles(directory=settings.STATIC["DIR"]), name="static"
)

# Include all views/routes
app.include_router(router)

# Include sub-ro
app.mount("/admin", admin_routes)
app.mount("/user", user_routes)
app.mount("/mc", minecraft_routes)


# Register Tortoise ORM
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


# Background polling loop
@app.on_event("startup")
async def start_polling():
    logger.info("Starting background polling loop.")
    asyncio.create_task(poll_server_status_loop(interval_seconds=120))
