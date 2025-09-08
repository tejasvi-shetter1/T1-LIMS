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

# ENHANCED VALIDATION ENDPOINT WITH PROPER ERROR HANDLING
@router.get("/{measurement_id}/validation")
async def validate_measurement_results(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    """
    Validate measurement results and determine if deviation report is needed
    Enhanced with comprehensive error handling and validation logic
    """
    try:
        from app.models.measurements import Measurement, UncertaintyCalculation
        
        # Check if measurement exists
        measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
        if not measurement:
            raise HTTPException(status_code=404, detail="Measurement not found")
        
        # Check if uncertainty calculation exists
        uncertainty = db.query(UncertaintyCalculation).filter(
            UncertaintyCalculation.measurement_id == measurement_id
        ).first()
        
        if not uncertainty:
            return {
                "measurement_id": measurement_id,
                "validation_status": "incomplete",
                "reason": "Uncertainty calculation not found - run calculate-uncertainty first",
                "deviation_report_required": False,
                "next_steps": ["Complete uncertainty calculation", "Re-run validation"]
            }
        
        # Perform comprehensive validation
        validation_result = perform_measurement_validation(measurement, uncertainty)
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        # Enhanced error logging for debugging
        error_detail = f"Validation processing failed for measurement {measurement_id}: {str(e)}"
        print(f"{error_detail}")
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Internal validation error",
                "message": error_detail,
                "measurement_id": measurement_id
            }
        )

def perform_measurement_validation(measurement, uncertainty):
    """
    Comprehensive measurement validation against ISO requirements
    """
    try:
        # Extract measurement data safely
        measurement_data = measurement.measurement_data or {}
        
        # Initialize validation checks
        validation_checks = {}
        
        # Check 1: Measurement completion
        validation_checks["measurement_complete"] = measurement.is_completed or False
        
        # Check 2: Uncertainty components available
        validation_checks["uncertainty_calculated"] = uncertainty is not None
        
        # Check 3: Required uncertainty components present
        if uncertainty:
            has_uncertainty_components = any([
                uncertainty.uncertainty_repeatability,
                uncertainty.uncertainty_reproducibility,
                uncertainty.uncertainty_output_drive,
                uncertainty.uncertainty_standard
            ])
            validation_checks["uncertainty_components_present"] = has_uncertainty_components
        else:
            validation_checks["uncertainty_components_present"] = False
        
        # Check 4: Expanded uncertainty calculated
        if uncertainty and uncertainty.expanded_uncertainty_percent:
            validation_checks["expanded_uncertainty_available"] = True
            # Check if within typical laboratory limits (example: < 5%)
            expanded_uncertainty_pct = float(uncertainty.expanded_uncertainty_percent)
            validation_checks["within_typical_limits"] = expanded_uncertainty_pct < 5.0
        else:
            validation_checks["expanded_uncertainty_available"] = False
            validation_checks["within_typical_limits"] = False
        
        # Check 5: Coverage factor appropriate (k=2 for 95% confidence)
        validation_checks["coverage_factor_appropriate"] = uncertainty.coverage_factor == 2 if uncertainty else False
        
        # Determine overall validation status
        critical_checks = [
            "measurement_complete",
            "uncertainty_calculated", 
            "expanded_uncertainty_available"
        ]
        
        all_critical_passed = all(validation_checks.get(check, False) for check in critical_checks)
        all_checks_passed = all(validation_checks.values())
        
        # Determine validation status
        if all_checks_passed:
            status = "passed"
            recommendation = "Measurement meets all ISO requirements - ready for certification"
        elif all_critical_passed:
            status = "passed_with_notes"
            recommendation = "Measurement meets critical requirements - minor issues noted"
        else:
            status = "failed"
            recommendation = "Measurement requires correction before certification"
        
        # Determine if deviation report needed
        deviation_required = not all_critical_passed or (
            uncertainty and 
            uncertainty.expanded_uncertainty_percent and 
            float(uncertainty.expanded_uncertainty_percent) > 3.0
        )
        
        return {
            "measurement_id": measurement.id,
            "measurement_type": measurement.measurement_type,
            "validation_status": status,
            "validation_checks": validation_checks,
            "summary": {
                "total_checks": len(validation_checks),
                "passed_checks": sum(validation_checks.values()),
                "critical_checks_passed": all_critical_passed
            },
            "uncertainty_summary": {
                "combined_uncertainty": float(uncertainty.combined_uncertainty) if uncertainty and uncertainty.combined_uncertainty else None,
                "expanded_uncertainty_percent": float(uncertainty.expanded_uncertainty_percent) if uncertainty and uncertainty.expanded_uncertainty_percent else None,
                "coverage_factor": uncertainty.coverage_factor if uncertainty else None
            },
            "deviation_report_required": deviation_required,
            "recommendation": recommendation,
            "timestamp": measurement.created_at.isoformat() if measurement.created_at else None
        }
        
    except Exception as e:
        # Fallback validation result on processing error
        return {
            "measurement_id": measurement.id,
            "validation_status": "error",
            "reason": f"Validation processing error: {str(e)}",
            "deviation_report_required": True,
            "recommendation": "Manual review required due to validation system error"
        }

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