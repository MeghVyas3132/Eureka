from fastapi import APIRouter

from api.v1.admin_plan_limits import router as admin_plan_limits_router
from api.v1.auth import router as auth_router
from api.v1.layouts import router as layouts_router
from api.v1.shelves import router as shelves_router
from api.v1.stores import router as stores_router
from api.v1.zones import router as zones_router

api_v1_router = APIRouter()
api_v1_router.include_router(admin_plan_limits_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(layouts_router)
api_v1_router.include_router(stores_router)
api_v1_router.include_router(zones_router)
api_v1_router.include_router(shelves_router)
