from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.standards_selection_service import StandardsSelectionService
from app.models.standards import Standard, JobStandard
from app.api.v1.auth import get_current_user
from app.models.users import User
from pydantic import BaseModel

router = APIRouter()

class StandardsSelectionRequest(BaseModel):
    job_id: Optional[int] = None
    equipment_desc: str
    range_min: float
    range_max: float
    unit: str

class StandardResponse(BaseModel):
    id: int
    nomenclature: str
    manufacturer: Optional[str]
    uncertainty: float
    unit: str
    range_min: Optional[float]
    range_max: Optional[float]
    certificate_no: Optional[str]
    calibration_valid_upto: str
    
    class Config:
        from_attributes = True

@router.post("/auto-select")
async def auto_select_standards(
    selection_request: StandardsSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Auto-select standards for given equipment and range"""
    
    try:
        selected_standards = StandardsSelectionService.auto_select_standards_for_job(
            db=db,
            job_id=selection_request.job_id or 0,
            equipment_desc=selection_request.equipment_desc,
            range_min=selection_request.range_min,
            range_max=selection_request.range_max,
            unit=selection_request.unit
        )
        
        result = []
        for item in selected_standards:
            standard = item['standard']
            result.append({
                'id': standard.id,
                'nomenclature': standard.nomenclature,
                'manufacturer': standard.manufacturer,
                'uncertainty': float(standard.uncertainty),
                'unit': standard.unit,
                'range_min': float(standard.range_min) if standard.range_min else None,
                'range_max': float(standard.range_max) if standard.range_max else None,
                'certificate_no': standard.certificate_no,
                'calibration_valid_upto': standard.calibration_valid_upto.isoformat(),
                'selection_reason': item['selection_reason'],
                'sequence': item['sequence']
            })
        
        return {
            "success": True,
            "selected_standards": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/available-for-equipment")
async def get_available_standards_for_equipment(
    equipment_desc: str = Query(...),
    range_min: float = Query(...),
    range_max: float = Query(...),
    unit: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available standards for manual selection"""
    
    try:
        available_standards = StandardsSelectionService.get_available_standards_for_equipment(
            db=db,
            equipment_desc=equipment_desc,
            range_min=range_min,
            range_max=range_max,
            unit=unit
        )
        
        result = []
        for item in available_standards:
            standard = item['standard']
            result.append({
                'id': standard.id,
                'nomenclature': standard.nomenclature,
                'manufacturer': standard.manufacturer,
                'uncertainty': float(standard.uncertainty),
                'coverage_ratio': item['coverage_ratio'],
                'is_optimal': item['is_optimal'],
                'validity_days': item['validity_days'],
                'discipline_match': item['discipline_match']
            })
        
        return {
            "success": True,
            "available_standards": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/job/{job_id}/standards")
async def get_job_standards(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get standards assigned to a job"""
    
    job_standards = db.query(JobStandard).filter(
        JobStandard.job_id == job_id
    ).order_by(JobStandard.standard_sequence).all()
    
    result = []
    for js in job_standards:
        result.append({
            'id': js.id,
            'standard_id': js.standard_id,
            'nomenclature': js.standard.nomenclature,
            'manufacturer': js.standard.manufacturer,
            'sequence': js.standard_sequence,
            'is_primary': js.is_primary,
            'auto_selected': js.auto_selected,
            'selection_reason': js.selection_reason,
            'uncertainty': float(js.standard.uncertainty)
        })
    
    return {
        "job_id": job_id,
        "standards": result,
        "total_count": len(result)
    }

@router.put("/job/{job_id}/standards/refresh")
async def refresh_job_standards(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh standards selection for a job"""
    
    from app.models.jobs import Job
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    srf_item = job.inward.srf_item
    
    # Parse range from existing data
    from app.services.inward_service import InwardService
    range_info = InwardService._parse_equipment_range(srf_item.range_text)
    
    try:
        # Re-select standards
        selected_standards = StandardsSelectionService.auto_select_standards_for_job(
            db=db,
            job_id=job_id,
            equipment_desc=srf_item.equip_desc,
            range_min=range_info['min'],
            range_max=range_info['max'],
            unit=srf_item.unit or "Nm"
        )
        
        # Create new job standards (this will remove old auto-selected ones)
        StandardsSelectionService.create_job_standards(db, job_id, selected_standards)
        
        return {
            "success": True,
            "message": f"Standards refreshed. Selected {len(selected_standards)} standards.",
            "selected_count": len(selected_standards)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
