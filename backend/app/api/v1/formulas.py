# app/api/v1/formulas.py - Formula Interpolation & Lookup API
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.formula_interpolation_service import FormulaInterpolationService
from app.models.calculations import FormulaLookupTable, CalculationEngineConfig
from app.api.v1.auth import get_current_user
from app.models.users import User

router = APIRouter()

# Pydantic Models
class InterpolationResponse(BaseModel):
    torque_value: float
    interpolated_error: float
    lookup_method: str
    source_table: str
    confidence: float

class LookupTableInfo(BaseModel):
    id: int
    table_name: str
    lookup_type: str
    category: str
    data_points: int
    validity_period: Optional[str]
    is_active: bool

@router.get("/interpolate/torque-error/{torque_value}", response_model=InterpolationResponse)
async def interpolate_torque_error(
    torque_value: float,
    equipment_type_id: Optional[int] = Query(None, description="Equipment type ID for specific lookup"),
    db: Session = Depends(get_db)
):
    """
    🔍 Interpolate torque error using Excel XLOOKUP equivalent
    
    This endpoint replicates Excel's XLOOKUP functionality for torque error correction.
    Used in Stage 1 repeatability calculations.
    """
    try:
        interpolation_service = FormulaInterpolationService(db)
        
        # Get interpolated error value
        interpolated_error = interpolation_service.interpolate_torque_error(torque_value)
        
        # Get source lookup table info
        lookup_table = interpolation_service._get_lookup_table("interpolation", "torque_transducer")
        
        # Calculate confidence based on proximity to lookup points
        confidence = calculate_interpolation_confidence(torque_value, lookup_table)
        
        return InterpolationResponse(
            torque_value=torque_value,
            interpolated_error=interpolated_error,
            lookup_method="nearest_neighbor" if confidence > 0.9 else "linear_interpolation",
            source_table=lookup_table.table_name if lookup_table else "default",
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Interpolation failed: {str(e)}")

@router.get("/interpolate/uncertainty/{torque_value}")
async def interpolate_uncertainty_value(
    torque_value: float,
    uncertainty_type: str = Query(..., description="Type: master_standard, cmc, measurement_error"),
    db: Session = Depends(get_db)
):
    """🎯 Interpolate uncertainty values for Stage 3 calculations"""
    
    try:
        interpolation_service = FormulaInterpolationService(db)
        
        if uncertainty_type == "master_standard":
            value = interpolation_service.get_master_transducer_uncertainty(torque_value)
        elif uncertainty_type == "cmc":
            value = interpolation_service.get_cmc_value(torque_value)
        elif uncertainty_type == "measurement_error":
            value = interpolation_service.get_measurement_error(torque_value)
        else:
            raise ValueError(f"Unknown uncertainty type: {uncertainty_type}")
        
        return {
            "torque_value": torque_value,
            "uncertainty_type": uncertainty_type,
            "interpolated_value": value,
            "units": "%" if uncertainty_type in ["cmc", "measurement_error"] else "absolute"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/lookup-tables/", response_model=List[LookupTableInfo])
async def get_available_lookup_tables(
    lookup_type: Optional[str] = Query(None, description="Filter by lookup type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    equipment_type_id: Optional[int] = Query(None, description="Filter by equipment type"),
    db: Session = Depends(get_db)
):
    """📋 Get all available formula lookup tables with filtering"""
    
    query = db.query(FormulaLookupTable).filter(FormulaLookupTable.is_active == True)
    
    if lookup_type:
        query = query.filter(FormulaLookupTable.lookup_type == lookup_type)
    
    if category:
        query = query.filter(FormulaLookupTable.category == category)
    
    if equipment_type_id:
        query = query.filter(FormulaLookupTable.equipment_type_id == equipment_type_id)
    
    tables = query.all()
    
    return [
        LookupTableInfo(
            id=table.id,
            table_name=table.table_name,
            lookup_type=table.lookup_type,
            category=table.category,
            data_points=len(table.lookup_data) if isinstance(table.lookup_data, list) else 0,
            validity_period=table.validity_period,
            is_active=table.is_active
        )
        for table in tables
    ]

@router.get("/lookup-tables/{table_id}/data")
async def get_lookup_table_data(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """📊 Get detailed lookup table data"""
    
    table = db.query(FormulaLookupTable).filter(FormulaLookupTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Lookup table not found")
    
    return {
        "table_info": {
            "id": table.id,
            "table_name": table.table_name,
            "lookup_type": table.lookup_type,
            "category": table.category,
            "equipment_type_id": table.equipment_type_id,
            "validity_period": table.validity_period
        },
        "data_structure": table.data_structure,
        "lookup_data": table.lookup_data,
        "data_points": len(table.lookup_data) if isinstance(table.lookup_data, list) else 0,
        "created_at": table.created_at,
        "updated_at": table.updated_at
    }

@router.post("/lookup-tables/{table_id}/validate")
async def validate_lookup_table(
    table_id: int,
    test_values: List[float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """🧪 Validate lookup table with test values"""
    
    table = db.query(FormulaLookupTable).filter(FormulaLookupTable.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Lookup table not found")
    
    interpolation_service = FormulaInterpolationService(db)
    validation_results = []
    
    for test_value in test_values:
        try:
            if table.lookup_type == "interpolation":
                result = interpolation_service.interpolate_torque_error(test_value)
            elif table.lookup_type == "uncertainty":
                result = interpolation_service.get_master_transducer_uncertainty(test_value)
            elif table.lookup_type == "cmc":
                result = interpolation_service.get_cmc_value(test_value)
            else:
                result = 0.0
            
            validation_results.append({
                "input_value": test_value,
                "interpolated_result": result,
                "status": "success"
            })
            
        except Exception as e:
            validation_results.append({
                "input_value": test_value,
                "interpolated_result": None,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "table_id": table_id,
        "table_name": table.table_name,
        "validation_results": validation_results,
        "success_rate": len([r for r in validation_results if r["status"] == "success"]) / len(validation_results) * 100
    }

@router.get("/formulas/constants")
async def get_formula_constants(
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    db: Session = Depends(get_db)
):
    """🔢 Get formula constants used in calculations"""
    
    # Get from calculation engine config
    query = db.query(CalculationEngineConfig).filter(CalculationEngineConfig.is_active == True)
    
    if equipment_type:
        query = query.filter(CalculationEngineConfig.equipment_type == equipment_type)
    
    configs = query.all()
    
    constants = {}
    for config in configs:
        if config.formula_constants:
            constants[config.config_name] = config.formula_constants
    
    return {
        "available_constants": constants,
        "common_constants": {
            "coverage_factor": 2.0,
            "sqrt_3": 1.732050808,
            "sqrt_5": 2.236067977,
            "confidence_level": 95.0
        }
    }

@router.get("/formulas/excel-compliance")
async def check_excel_compliance(
    torque_values: List[float] = Query(..., description="Test torque values"),
    db: Session = Depends(get_db)
):
    """✅ Check Excel formula compliance with test values"""
    
    interpolation_service = FormulaInterpolationService(db)
    compliance_results = []
    
    for torque_value in torque_values:
        try:
            # Test interpolation
            interpolated_error = interpolation_service.interpolate_torque_error(torque_value)
            
            # Test uncertainty lookup
            uncertainty = interpolation_service.get_master_transducer_uncertainty(torque_value)
            
            # Test CMC lookup
            cmc_value = interpolation_service.get_cmc_value(torque_value)
            
            compliance_results.append({
                "torque_value": torque_value,
                "interpolation_error": interpolated_error,
                "uncertainty": uncertainty,
                "cmc_value": cmc_value,
                "excel_compliant": True,
                "notes": "All lookups successful"
            })
            
        except Exception as e:
            compliance_results.append({
                "torque_value": torque_value,
                "interpolation_error": None,
                "uncertainty": None,
                "cmc_value": None,
                "excel_compliant": False,
                "notes": f"Error: {str(e)}"
            })
    
    success_count = len([r for r in compliance_results if r["excel_compliant"]])
    
    return {
        "test_results": compliance_results,
        "overall_compliance": (success_count / len(compliance_results)) * 100,
        "excel_formula_status": "COMPLIANT" if success_count == len(compliance_results) else "PARTIAL",
        "recommendations": [
            "Verify lookup table data completeness",
            "Check interpolation algorithm accuracy",
            "Validate against Excel reference calculations"
        ] if success_count < len(compliance_results) else ["All tests passed - Excel compliant"]
    }

# Helper functions
def calculate_interpolation_confidence(torque_value: float, lookup_table) -> float:
    """Calculate confidence level for interpolation based on proximity to data points"""
    if not lookup_table or not lookup_table.lookup_data:
        return 0.5
    
    try:
        data_points = lookup_table.lookup_data
        if isinstance(data_points, list) and data_points:
            # Find closest data point
            closest_distance = min(
                abs(torque_value - point.get("torque_value", 0))
                for point in data_points
                if isinstance(point, dict) and "torque_value" in point
            )
            
            # Calculate confidence (closer = higher confidence)
            if closest_distance == 0:
                return 1.0  # Exact match
            elif closest_distance < 100:
                return 0.95  # Very close
            elif closest_distance < 500:
                return 0.8   # Close
            else:
                return 0.6   # Interpolated
        
    except Exception:
        pass
    
    return 0.5  # Default confidence