from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:Aimlsn%%402025@localhost/nepl_lims_local"
    
    # Application
    SECRET_KEY: str = "nepl-lims-local-dev-secret-key-2025"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NEPL LIMS"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000"
    ]
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True

settings = Settings()
