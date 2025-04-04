import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.cache import poll_server_status_loop
from app.views import router

app = FastAPI()

# 🔐 Add session middleware (required for login sessions)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)

# Static files (e.g., downloads)
app.mount(config.STATIC['URL'], StaticFiles(directory=config.STATIC['DIR']), name="static")

# Include all views/routes
app.include_router(router)

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
    asyncio.create_task(poll_server_status_loop(interval_seconds=60))
