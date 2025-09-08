from fastapi import APIRouter
from app.api.v1 import auth, srf, inward, measurements, deviations, certificates  # Add auth

api_router = APIRouter()

# Register all API routers with their respective prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])  # NEW: Authentication endpoints
api_router.include_router(srf.router, prefix="/srf", tags=["srf"])
api_router.include_router(inward.router, prefix="/inward", tags=["inward"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
api_router.include_router(deviations.router, prefix="/deviations", tags=["deviations"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
