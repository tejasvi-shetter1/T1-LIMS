# backend/app/schemas/inward.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime  # Import both

class InwardBase(BaseModel):
    srf_item_id: int
    inward_date: Optional[date] = None
    customer_dc_no: Optional[str] = None
    customer_dc_date: Optional[date] = None
    condition_on_receipt: str = "satisfactory"
    visual_inspection_notes: Optional[str] = None
    supplier: Optional[str] = None
    quantity_received: int = 1
    received_by: Optional[str] = None

class InwardCreate(InwardBase):
    pass

class InwardResponse(InwardBase):
    id: int
    nepl_id: str
    status: str
    barcode: Optional[str] = None
    created_at: datetime  # Change from date to datetime
    
    # SRF Item details (joined)
    srf_no: Optional[str] = None
    customer_name: Optional[str] = None
    equip_desc: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    serial_no: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
