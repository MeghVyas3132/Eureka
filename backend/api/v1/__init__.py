from fastapi import APIRouter

from api.v1.admin_plan_limits import router as admin_plan_limits_router
from api.v1.admin_users import router as admin_users_router
from api.v1.auth import router as auth_router
from api.v1.layouts import router as layouts_router

api_v1_router = APIRouter()
api_v1_router.include_router(admin_plan_limits_router)
api_v1_router.include_router(admin_users_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(layouts_router)
