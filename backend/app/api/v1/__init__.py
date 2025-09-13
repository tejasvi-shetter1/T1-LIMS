
from fastapi import APIRouter

from app.api.v1 import (
    auth, srf, inward, measurements, deviations, certificates, standards,
    calculations, formulas, enhanced_deviations, auto_deviation
)

api_router = APIRouter()

# Register all API routers with their respective prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(srf.router, prefix="/srf", tags=["srf"])
api_router.include_router(inward.router, prefix="/inward", tags=["inward"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
api_router.include_router(deviations.router, prefix="/deviations", tags=["deviations"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(standards.router, prefix="/standards", tags=["standards"])

# Phase 2 Enhanced APIs - Calculation Engine
api_router.include_router(calculations.router, prefix="/calculations", tags=["calculations"])
api_router.include_router(formulas.router, prefix="/formulas", tags=["formulas"])
api_router.include_router(enhanced_deviations.router, prefix="/enhanced-deviations", tags=["enhanced-deviations"])

# Phase 3 Auto-Deviation System
api_router.include_router(auto_deviation.router, prefix="/auto-deviation", tags=["auto-deviation"])
