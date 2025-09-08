from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.crud.inward import InwardCrud
from app.services.inward_service import InwardService  # NEW: Dynamic Service
from app.schemas.inward import InwardCreate, InwardResponse
from app.api.v1.auth import get_current_user  # NEW: Authentication
from app.models.users import User  # NEW: User model

router = APIRouter()

@router.post("/", response_model=InwardResponse)
async def create_inward_entry(
    inward_data: InwardCreate,
    current_user: User = Depends(get_current_user),  # NEW: Authentication
    db: Session = Depends(get_db)
):
    """Create inward entry with DYNAMIC job generation"""
    try:
        # NEW: Use dynamic service instead of hardcoded CRUD
        inward = InwardService.create_inward_with_dynamic_job(
            db=db, 
            inward_data=inward_data, 
            current_user=current_user.username
        )
        return inward
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[InwardResponse])
async def get_inward_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),  # NEW: Authentication
    db: Session = Depends(get_db)
):
    """Get paginated inward list"""
    inwards = InwardCrud.get_inward_list(db=db, skip=skip, limit=limit)
    return inwards

@router.get("/{inward_id}", response_model=InwardResponse) 
async def get_inward_by_id(
    inward_id: int,
    current_user: User = Depends(get_current_user),  # NEW: Authentication
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
    current_user: User = Depends(get_current_user),  # NEW: Authentication
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
    current_user: User = Depends(get_current_user),  # NEW: Authentication
    db: Session = Depends(get_db)
):
    """Update condition assessment with DYNAMIC job creation"""
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
        
        # NEW: Auto-create job using DYNAMIC logic if not exists
        if not inward.job:
            try:
                job = InwardService._create_dynamic_job(db, inward, current_user.username)
                print(f"Dynamic job {job.job_number} created for condition update")
            except Exception as e:
                print(f"Failed to create dynamic job: {e}")
                # Fallback to generic job creation
                job = InwardService._create_generic_job(db, inward, current_user.username)
    else:
        inward.status = "inspection_complete"
    
    db.commit()
    
    return {"message": "Condition assessment updated", "condition": condition}

# NEW: Equipment Detection Endpoint
@router.get("/{inward_id}/equipment-detection")
async def get_equipment_detection(
    inward_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get equipment type detection results for inward item"""
    from app.models.inward import Inward
    from app.services.equipment_service import EquipmentService
    
    inward = db.query(Inward).filter(Inward.id == inward_id).first()
    if not inward:
        raise HTTPException(status_code=404, detail="Inward entry not found")
    
    srf_item = inward.srf_item
    if not srf_item:
        raise HTTPException(status_code=404, detail="SRF item not found")
    
    # Run equipment detection
    equipment_type = EquipmentService.auto_detect_equipment_type(
        db=db,
        nomenclature=srf_item.equip_desc,
        range_text=srf_item.range_text,
        unit=srf_item.unit
    )
    
    if equipment_type:
        # Get measurement template
        template = EquipmentService.get_measurement_template(db, equipment_type.id)
        
        # Get applicable standards
        range_min, range_max = EquipmentService._parse_range(srf_item.range_text) if srf_item.range_text else (None, None)
        standards = EquipmentService.get_applicable_standards(
            db, equipment_type.id, (range_min, range_max) if range_min else None
        )
        
        return {
            "detected": True,
            "equipment_type": {
                "id": equipment_type.id,
                "name": equipment_type.nomenclature,
                "category": equipment_type.category.name,
                "classification": equipment_type.classification,
                "calibration_method": equipment_type.calibration_method,
                "unit": equipment_type.unit,
                "range": f"{equipment_type.min_range}-{equipment_type.max_range}"
            },
            "measurement_template": {
                "id": template.id,
                "name": template.template_name,
                "measurement_points": template.measurement_points,
                "readings_per_point": template.readings_per_point,
                "required_measurements": template.required_measurements
            } if template else None,
            "applicable_standards": standards,
            "input_data": {
                "nomenclature": srf_item.equip_desc,
                "range_text": srf_item.range_text,
                "unit": srf_item.unit
            }
        }
    else:
        return {
            "detected": False,
            "message": "No matching equipment type found",
            "input_data": {
                "nomenclature": srf_item.equip_desc,
                "range_text": srf_item.range_text,
                "unit": srf_item.unit
            },
            "suggestions": [
                "Verify equipment nomenclature spelling",
                "Check if equipment type is registered in system",
                "Contact administrator to add new equipment type"
            ]
        }
