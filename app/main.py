import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

from app.cache import poll_server_status_loop
from app.views import router

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.on_event("startup")
async def start_polling():
    asyncio.create_task(poll_server_status_loop(interval_seconds=60))
