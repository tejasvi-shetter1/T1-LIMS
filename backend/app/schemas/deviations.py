from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class DeviationCreate(BaseModel):
    job_id: int
    deviation_type: str
    severity: Optional[str] = "medium"
    description: str
    technical_impact: Optional[str] = None
    customer_impact: Optional[str] = None
    identified_by: str

class CustomerResponseUpdate(BaseModel):
    client_decision: str  # "ACCEPT" or "REJECT"
    client_comments: Optional[str] = None

class DeviationResponse(BaseModel):
    id: int
    job_id: int
    deviation_number: str
    deviation_type: Optional[str]
    severity: Optional[str]
    description: str
    status: Optional[str]
    identified_by: Optional[str]
    client_decision: Optional[str]
    client_comments: Optional[str]
    client_notified_at: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeviationActionResponse(BaseModel):
    id: int
    action_type: str
    action_by: str
    action_at: datetime
    comments: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    
    class Config:
        from_attributes = True