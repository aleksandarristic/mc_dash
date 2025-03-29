from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise
from app.views import router
from app.cache import get_server_status  # so startup runs at least once

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

