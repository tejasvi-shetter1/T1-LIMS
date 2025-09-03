from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class CertificateTypeEnum(str, Enum):
    CRT1 = "Crt1"
    CRT2 = "Crt2"
    CRT3 = "Crt3"

class GenerationStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CertificateCreate(BaseModel):
    job_id: int
    template_type: CertificateTypeEnum = CertificateTypeEnum.CRT1
    manual_overrides: Optional[Dict[str, Any]] = None

class CertificateGenerate(BaseModel):
    job_id: int
    template_type: str = "Crt1"
    include_password_protection: bool = True
    custom_fields: Optional[Dict[str, Any]] = None

class CertificateTemplateResponse(BaseModel):
    id: int
    template_name: str
    template_type: str
    equipment_types: Optional[List[str]] = None
    is_active: bool
    version: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CertificateResponse(BaseModel):
    id: int
    job_id: int
    certificate_number: str
    ulr_number: Optional[str]
    certificate_type: Optional[str]
    issue_date: date
    calibration_date: date
    recommended_due_date: Optional[date]
    generation_status: str
    status: str
    file_size_bytes: Optional[int]
    password_protected: bool
    download_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CertificateDetailResponse(CertificateResponse):
    template_id: Optional[int]
    certificate_data: Optional[Dict[str, Any]]
    generation_error: Optional[str]
    reviewed_by: Optional[str]
    approved_by: Optional[str]
    delivery_method: Optional[str]
    delivered_at: Optional[date]

class CertificateDownloadResponse(BaseModel):
    certificate_id: int
    filename: str
    content_type: str = "application/pdf"
    download_url: str
    requires_password: bool = False
