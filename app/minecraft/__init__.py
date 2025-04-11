from fastapi import FastAPI

from app.minecraft.views import router

minecraft_routes = FastAPI()
minecraft_routes.include_router(router)
