from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.crud.inward import InwardCrud
from app.schemas.inward import InwardCreate, InwardResponse

router = APIRouter()

@router.post("/", response_model=InwardResponse)
async def create_inward_entry(
    inward_data: InwardCreate,
    db: Session = Depends(get_db)
):
    """Create inward entry for SRF item"""
    try:
        inward = InwardCrud.create_inward(db=db, inward_data=inward_data)
        return inward
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[InwardResponse])
async def get_inward_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated inward list"""
    inwards = InwardCrud.get_inward_list(db=db, skip=skip, limit=limit)
    return inwards

@router.get("/{inward_id}", response_model=InwardResponse) 
async def get_inward_by_id(
    inward_id: int,
    db: Session = Depends(get_db)
):
    """Get inward entry by ID"""
    from app.models.inward import Inward
    inward = db.query(Inward).filter(Inward.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    return inward

@router.post("/{inward_id}/photos")
async def upload_condition_photos(
    inward_id: int,
    photos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload condition assessment photos"""
    from app.models.inward import Inward
    import os
    import uuid
    
    inward = db.query(Inward).filter(Inward.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    
    # Create upload directory if it doesn't exist
    upload_dir = "uploads/inward_photos"
    os.makedirs(upload_dir, exist_ok=True)
    
    photo_paths = []
    for photo in photos:
        # Generate unique filename
        file_ext = photo.filename.split(".")[-1]
        filename = f"{inward.nepl_id}_{uuid.uuid4().hex}.{file_ext}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save file
        with open(filepath, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
        
        photo_paths.append(filepath)
    
    # Update inward record with photo paths
    current_photos = inward.photos or []
    current_photos.extend(photo_paths)
    inward.photos = current_photos
    
    db.commit()
    
    return {"message": f"Uploaded {len(photos)} photos", "photo_paths": photo_paths}

@router.put("/{inward_id}/condition")
async def update_condition_assessment(
    inward_id: int,
    condition: str,
    inspection_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update condition assessment"""
    from app.models.inward import Inward
    
    inward = db.query(Inward).filter(Inward.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    
    inward.condition_on_receipt = condition
    if inspection_notes:
        inward.visual_inspection_notes = inspection_notes
    
    # Update status based on condition
    if condition == "satisfactory":
        inward.status = "ready_for_calibration"
        # Auto-create job if not exists
        if not inward.job:
            InwardCrud.create_job_from_inward(db, inward_id)
    else:
        inward.status = "inspection_complete"
    
    db.commit()
    
    return {"message": "Condition assessment updated", "condition": condition}
