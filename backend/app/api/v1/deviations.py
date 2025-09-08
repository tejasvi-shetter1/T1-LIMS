from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.deviations import DeviationReport
from app.schemas.deviations import DeviationCreate, DeviationResponse, CustomerResponseUpdate, DeviationActionResponse
from app.services.deviation_service import DeviationService
router = APIRouter()

@router.post("/", response_model=DeviationResponse)
async def create_deviation(
    deviation_data: DeviationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create new deviation"""
    try:
        deviation = DeviationService.create_deviation(db=db, deviation_data=deviation_data)
        
        # TODO: Add notification service call here
        # background_tasks.add_task(NotificationService.send_deviation_notification, deviation.id)
        
        return deviation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DeviationResponse])
async def get_deviations(
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get deviations with filters"""
    query = db.query(DeviationReport)
    
    if job_id:
        query = query.filter(DeviationReport.job_id == job_id)
    if status:
        query = query.filter(DeviationReport.status == status)
        
    deviations = query.offset(skip).limit(limit).all()
    return deviations

@router.get("/{deviation_id}", response_model=DeviationResponse)
async def get_deviation_details(
    deviation_id: int,
    db: Session = Depends(get_db)
):
    """Get deviation details"""
    deviation = db.query(DeviationReport).filter(DeviationReport.id == deviation_id).first()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found")
    return deviation

@router.put("/{deviation_id}/customer-response")
async def update_customer_response(
    deviation_id: int,
    response_data: CustomerResponseUpdate,
    db: Session = Depends(get_db)
):
    """Customer response to deviation"""
    try:
        current_user = "customer_user"  # TODO: Get from JWT token
        
        deviation = DeviationService.update_customer_response(
            db=db,
            deviation_id=deviation_id,
            response_data=response_data,
            customer_user=current_user
        )
        
        return {"message": "Response recorded successfully", "status": deviation.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{deviation_id}/resolve")
async def resolve_deviation(
    deviation_id: int,
    resolution_data: dict,
    db: Session = Depends(get_db)
):
    """Resolve deviation"""
    try:
        current_user = "qa_manager"  # TODO: Get from JWT token
        
        deviation = DeviationService.resolve_deviation(
            db=db,
            deviation_id=deviation_id,
            resolution_actions=resolution_data["resolution_actions"],
            resolved_by=current_user
        )
        
        return {"message": "Deviation resolved successfully", "deviation_id": deviation.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{deviation_id}/audit-trail", response_model=List[DeviationActionResponse])
async def get_deviation_audit_trail(
    deviation_id: int,
    db: Session = Depends(get_db)
):
    """Get deviation audit trail"""
    from app.models.deviations import DeviationAction
    
    audit_trail = db.query(DeviationAction).filter(
        DeviationAction.deviation_id == deviation_id
    ).order_by(DeviationAction.action_at.desc()).all()
    
    return audit_trail