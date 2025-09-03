from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html


# Create FastAPI app
app = FastAPI(
    title="NEPL LIMS API",
    description="Calibration Certificate Tracking & Management System",
    version="1.0.0"
)


app.add_middleware(GZipMiddleware, minimum_size=1000)


# Import routers - ADDED deviations import
from app.api.v1 import srf, inward, measurements, deviations, certificates


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_ui_parameters={
            "syntaxHighlight": False,  # Disable syntax highlighting
            "defaultModelRendering": "model"  # Show schema instead of examples
        }
    )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "NEPL LIMS API v1.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


# Include routers - ADDED deviations router
app.include_router(srf.router, prefix=f"{settings.API_V1_STR}/srf", tags=["SRF"])
app.include_router(inward.router, prefix=f"{settings.API_V1_STR}/inward", tags=["Inward"])
app.include_router(measurements.router, prefix=f"{settings.API_V1_STR}/measurements", tags=["Measurements"])
app.include_router(deviations.router, prefix=f"{settings.API_V1_STR}/deviations", tags=["Deviations"])
app.include_router(certificates.router, prefix=f"{settings.API_V1_STR}/certificates", tags=["Certificates"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
