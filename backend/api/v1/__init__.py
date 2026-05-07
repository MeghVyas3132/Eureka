from fastapi import APIRouter

from api.v1.admin_onboarding import router as admin_onboarding_router
from api.v1.admin_plan_limits import router as admin_plan_limits_router
from api.v1.admin_stats import router as admin_stats_router
from api.v1.admin_users import router as admin_users_router
from api.v1.auth import router as auth_router
from api.v1.layouts import router as layouts_router
from api.v1.planograms import router as planograms_router
from api.v1.products import router as products_router
from api.v1.products_import import router as products_import_router
from api.v1.sales import router as sales_router
from api.v1.sales_import import router as sales_import_router
from api.v1.shelves import router as shelves_router
from api.v1.stores import router as stores_router
from api.v1.zones import router as zones_router

api_v1_router = APIRouter()
api_v1_router.include_router(admin_onboarding_router)
api_v1_router.include_router(admin_plan_limits_router)
api_v1_router.include_router(admin_stats_router)
api_v1_router.include_router(admin_users_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(layouts_router)
api_v1_router.include_router(planograms_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(products_import_router)
api_v1_router.include_router(sales_router)
api_v1_router.include_router(sales_import_router)
api_v1_router.include_router(stores_router)
api_v1_router.include_router(zones_router)
api_v1_router.include_router(shelves_router)
