from fastapi import FastAPI

from app.admin.views import router

admin_routes = FastAPI()
admin_routes.include_router(router)
