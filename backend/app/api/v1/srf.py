from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.srf import SRFCreate, SRFResponse, SRFUpdate

router = APIRouter()

@router.post("/", response_model=SRFResponse, status_code=status.HTTP_201_CREATED)
async def create_srf(srf_data: SRFCreate, db: Session = Depends(get_db)):
    """Create new SRF with items"""
    try:
        from app.crud.srf import SRFCrud
        db_srf = SRFCrud.create_srf(db=db, srf_data=srf_data)
        return db_srf
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[SRFResponse])
async def get_srfs_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get paginated list of SRFs with customer details"""
    try:
        from app.crud.srf import SRFCrud
        srfs = SRFCrud.get_srfs_list(db=db, skip=skip, limit=limit)
        return srfs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SRFs: {str(e)}")

@router.get("/{srf_id}", response_model=SRFResponse)
async def get_srf_by_id(srf_id: int, db: Session = Depends(get_db)):
    """Get SRF by ID with all items"""
    try:
        from app.crud.srf import SRFCrud
        db_srf = SRFCrud.get_srf_by_id(db=db, srf_id=srf_id)
        if not db_srf:
            raise HTTPException(status_code=404, detail="SRF not found")
        return db_srf
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{srf_id}/status")
async def update_srf_status(
    srf_id: int, 
    new_status: str, 
    db: Session = Depends(get_db)
):
    """Update SRF status"""
    try:
        from app.crud.srf import SRFCrud
        db_srf = SRFCrud.update_srf_status(db=db, srf_id=srf_id, new_status=new_status)
        if not db_srf:
            raise HTTPException(status_code=404, detail="SRF not found")
        return {"message": "SRF status updated successfully", "srf_id": srf_id, "new_status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#  NEW ENDPOINT - Add this to your existing file
@router.get("/{srf_id}/items/{item_id}/inward-eligible")
async def check_inward_eligible(
    srf_id: int, 
    item_id: int, 
    db: Session = Depends(get_db)
):
    """Check if SRF item is eligible for inward processing"""
    try:
        from app.models.srf import SRFItem, SRF
        from app.models.inward import Inward
        
        srf_item = db.query(SRFItem).join(SRF).filter(
            SRFItem.id == item_id,
            SRFItem.srf_id == srf_id
        ).first()
        
        if not srf_item:
            raise HTTPException(status_code=404, detail="SRF item not found")
        
        eligibility_result = check_item_eligibility(db, srf_item)
        
        return {
            "eligible": eligibility_result["eligible"],
            "reason": eligibility_result["reason"],
            "srf_id": srf_id,
            "item_id": item_id,
            "srf_status": srf_item.srf.status,
            "item_description": srf_item.equip_desc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking eligibility: {str(e)}")

def check_item_eligibility(db: Session, srf_item) -> dict:
    """Core eligibility validation logic"""
    
    # Check 1: SRF must be in accepted state
    if srf_item.srf.status not in ["accepted", "approved"]:
        return {
            "eligible": False, 
            "reason": f"SRF status is '{srf_item.srf.status}', must be 'accepted' or 'approved'"
        }
    
    # Check 2: Item not already in inward
    from app.models.inward import Inward
    existing_inward = db.query(Inward).filter(Inward.srf_item_id == srf_item.id).first()
    if existing_inward:
        return {
            "eligible": False, 
            "reason": f"Item already registered in inward (ID: {existing_inward.id})"
        }
    
    # Check 3: Required fields present
    required_fields = [srf_item.equip_desc, srf_item.make, srf_item.serial_no]
    if not all(required_fields):
        missing = []
        if not srf_item.equip_desc: missing.append("equipment_description")
        if not srf_item.make: missing.append("make")
        if not srf_item.serial_no: missing.append("serial_number")
        return {
            "eligible": False, 
            "reason": f"Missing required fields: {', '.join(missing)}"
        }
    
    # All checks passed
    return {
        "eligible": True, 
        "reason": "All eligibility criteria met - ready for inward processing"
    }