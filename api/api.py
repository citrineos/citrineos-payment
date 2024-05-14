from fastapi import APIRouter

from api.endpoints.evses import router as evses_router
from api.endpoints.locations import router as locations_router
from api.endpoints.tariffs import router as tariffs_router
from api.endpoints.checkouts import router as checkouts_router
from api.endpoints.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(evses_router, prefix="/evses", tags=["evses"])
api_router.include_router(locations_router, prefix="/locations", tags=["locations"])
api_router.include_router(tariffs_router, prefix="/tariffs", tags=["tariffs"])
api_router.include_router(checkouts_router, prefix="/checkouts", tags=["checkouts"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
