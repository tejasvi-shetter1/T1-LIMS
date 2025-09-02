from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.measurement_service import MeasurementService
from app.services.uncertainty_service import UncertaintyCalculationService
from app.schemas.measurements import (
    MeasurementCreate, MeasurementResponse, 
    RepeatabilityData, ReproducibilityData,
    OutputDriveData, LoadingPointData,
    UncertaintyCalculationResponse
)

router = APIRouter()

@router.post("/repeatability", response_model=MeasurementResponse)
async def create_repeatability_measurement(
    measurement_data: RepeatabilityData,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Create repeatability measurement (Type A - 5 readings per point)
    Implements exact Excel calculations from Raw Data sheet
    """
    try:
        measurement = MeasurementService.create_repeatability_measurement(
            db=db,
            job_id=job_id,
            measurement_data=measurement_data
        )
        return measurement
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reproducibility", response_model=MeasurementResponse)
async def create_reproducibility_measurement(
    measurement_data: ReproducibilityData,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Create reproducibility measurement (Type B - 4 sequences)
    """
    try:
        measurement = MeasurementService.create_reproducibility_measurement(
            db=db,
            job_id=job_id,
            measurement_data=measurement_data
        )
        return measurement
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/output-drive", response_model=MeasurementResponse)
async def create_output_drive_measurement(
    measurement_data: OutputDriveData,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Create output drive geometric effect measurement (4 positions)
    """
    try:
        measurement = MeasurementService.create_output_drive_measurement(
            db=db,
            job_id=job_id,
            measurement_data=measurement_data.dict()
        )
        return measurement
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/job/{job_id}", response_model=List[MeasurementResponse])
async def get_job_measurements(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get all measurements for a job"""
    from app.models.measurements import Measurement
    
    measurements = db.query(Measurement).filter(Measurement.job_id == job_id).all()
    return measurements

@router.get("/{measurement_id}/uncertainty", response_model=List[UncertaintyCalculationResponse])
async def get_measurement_uncertainties(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """Get uncertainty calculations for a measurement"""
    from app.models.measurements import UncertaintyCalculation
    
    calculations = db.query(UncertaintyCalculation).filter(
        UncertaintyCalculation.measurement_id == measurement_id
    ).all()
    
    return calculations

@router.post("/{measurement_id}/calculate-uncertainty")
async def calculate_measurement_uncertainty(
    measurement_id: int,
    set_torque: float,
    db: Session = Depends(get_db)
):
    """
    Calculate complete uncertainty budget for a measurement
    Using exact Excel formulas from Uncertainty sheet
    """
    try:
        uncertainty_calc = UncertaintyCalculationService.calculate_torque_uncertainty_budget(
            db=db,
            measurement_id=measurement_id,
            set_torque=set_torque
        )
        
        db.add(uncertainty_calc)
        db.commit()
        db.refresh(uncertainty_calc)
        
        return {
            "message": "Uncertainty calculation completed",
            "uncertainty_id": uncertainty_calc.id,
            "combined_uncertainty": float(uncertainty_calc.combined_uncertainty),
            "expanded_uncertainty_percent": float(uncertainty_calc.expanded_uncertainty_percent),
            "expanded_uncertainty_absolute": float(uncertainty_calc.expanded_uncertainty_absolute)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{measurement_id}/validation")
async def validate_measurement_results(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """
    Validate measurement results and determine if deviation report is needed
    """
    from app.models.measurements import Measurement, UncertaintyCalculation
    
    measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    uncertainty = db.query(UncertaintyCalculation).filter(
        UncertaintyCalculation.measurement_id == measurement_id
    ).first()
    
    if not uncertainty:
        raise HTTPException(status_code=400, detail="Uncertainty calculation not found")
    
    validation_result = UncertaintyCalculationService.validate_measurement_results(
        measurement_data=measurement.measurement_data,
        uncertainty_calculation=uncertainty
    )
    
    return validation_result

@router.get("/templates/", response_model=List[dict])
async def get_measurement_templates(
    equipment_type: str = Query(..., description="torque, pressure, dimension"),
    db: Session = Depends(get_db)
):
    """Get measurement templates for equipment type"""
    from app.models.measurements import MeasurementTemplate
    
    templates = db.query(MeasurementTemplate).filter(
        MeasurementTemplate.equipment_type == equipment_type,
        MeasurementTemplate.is_active == True
    ).all()
    
    return [
        {
            "id": t.id,
            "template_name": t.template_name,
            "calibration_method": t.calibration_method,
            "measurement_points": t.measurement_points,
            "required_measurements": t.required_measurements,
            "readings_per_point": t.readings_per_point
        }
        for t in templates
    ]
