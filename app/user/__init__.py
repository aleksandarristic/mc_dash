from fastapi import FastAPI

from app.user.views import router

user_routes = FastAPI()
user_routes.include_router(router)
