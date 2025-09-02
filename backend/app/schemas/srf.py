# backend/app/schemas/srf.py
from pydantic import BaseModel, ConfigDict, validator
from typing import List, Optional
from datetime import date, datetime  # Import both
from enum import Enum

class SRFItemBase(BaseModel):
    equip_desc: str
    make: Optional[str] = None
    model: Optional[str] = None  
    serial_no: Optional[str] = None
    range_text: Optional[str] = None
    unit: Optional[str] = None
    calibration_points: Optional[str] = "AS PER STANDARD"
    calibration_mode: Optional[str] = "AS PER STANDARD"
    quantity: int = 1
    remarks: Optional[str] = None

class SRFItemCreate(SRFItemBase):
    pass

class SRFItemResponse(SRFItemBase):
    id: int
    sl_no: int
    srf_id: int
    
    model_config = ConfigDict(from_attributes=True)

class SRFBase(BaseModel):
    customer_id: int
    contact_person: Optional[str] = None
    date_received: Optional[date] = None
    priority: str = "normal"
    special_instructions: Optional[str] = None
    nextage_contract_reference: Optional[str] = None
    calibration_frequency: str = "as_per_standard"

class SRFCreate(SRFBase):
    items: List[SRFItemCreate]
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one item is required')
        return v

class SRFUpdate(BaseModel):
    contact_person: Optional[str] = None
    priority: Optional[str] = None
    special_instructions: Optional[str] = None

class SRFResponse(SRFBase):
    id: int
    srf_no: str
    status: str
    created_at: datetime  # Change from date to datetime
    items: List[SRFItemResponse] = []
    
    # Customer details (joined)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
