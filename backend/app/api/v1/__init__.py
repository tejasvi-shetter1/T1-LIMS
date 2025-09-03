from fastapi import APIRouter
from app.api.v1 import srf, inward, measurements, deviations, certificates

api_router = APIRouter()
api_router.include_router(srf.router, prefix="/srf", tags=["srf"])
api_router.include_router(inward.router, prefix="/inward", tags=["inward"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
api_router.include_router(deviations.router, prefix="/deviations", tags=["deviations"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])  # Add this
