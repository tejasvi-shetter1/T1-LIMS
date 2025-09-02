from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.crud.srf import SRFCrud
from app.schemas.srf import SRFCreate, SRFResponse, SRFUpdate

router = APIRouter()

@router.post("/", response_model=SRFResponse)
async def create_srf(
    srf_data: SRFCreate,
    db: Session = Depends(get_db)
):
    """Create new Service Request Form (SRF)"""
    try:
        srf = SRFCrud.create_srf(db=db, srf_data=srf_data)
        return srf
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[SRFResponse])
async def get_srfs_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated list of SRFs"""
    srfs = SRFCrud.get_srfs_list(db=db, skip=skip, limit=limit)
    return srfs

@router.get("/{srf_id}", response_model=SRFResponse)
async def get_srf_by_id(
    srf_id: int,
    db: Session = Depends(get_db)
):
    """Get SRF by ID with all items"""
    srf = SRFCrud.get_srf_by_id(db=db, srf_id=srf_id)
    if not srf:
        raise HTTPException(status_code=404, detail="SRF not found")
    return srf

@router.put("/{srf_id}/status")
async def update_srf_status(
    srf_id: int,
    new_status: str,
    db: Session = Depends(get_db)
):
    """Update SRF status"""
    srf = SRFCrud.update_srf_status(db=db, srf_id=srf_id, new_status=new_status)
    if not srf:
        raise HTTPException(status_code=404, detail="SRF not found")
    return {"message": "Status updated successfully", "srf_id": srf_id, "new_status": new_status}

@router.get("/{srf_id}/items/{item_id}/inward-eligible")
async def check_inward_eligible(
    srf_id: int,
    item_id: int,
    db: Session = Depends(get_db)
):
    """Check if SRF item is eligible for inward"""
    # Check if SRF is accepted and item doesn't have inward entry yet
    srf = SRFCrud.get_srf_by_id(db=db, srf_id=srf_id)
    if not srf:
        raise HTTPException(status_code=404, detail="SRF not found")
    
    if srf.status != "accepted":
        return {"eligible": False, "reason": "SRF not yet accepted"}
    
    # Check if item already has inward entry
    from app.models.inward import Inward
    existing_inward = db.query(Inward).filter(Inward.srf_item_id == item_id).first()
    
    if existing_inward:
        return {"eligible": False, "reason": "Item already has inward entry"}
    
    return {"eligible": True, "reason": "Ready for inward"}
