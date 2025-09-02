from pydantic import BaseModel, validator
from typing import List, Dict, Optional, Any
from datetime import date
from decimal import Decimal
#from sqlalchemy.types import DECIMAL as Decimal

class MeasurementPointData(BaseModel):
    set_torque: float
    set_pressure: Optional[float] = None
    readings: List[float]  # 5 readings for repeatability
    
    @validator('readings')
    def validate_readings(cls, v):
        if len(v) != 5:
            raise ValueError('Exactly 5 readings required for repeatability test')
        return v

class RepeatabilityData(BaseModel):
    calibration_date: date
    nepl_work_id: str
    measurement_points: List[MeasurementPointData]  # Typically 3 points (20%, 60%, 100%)
    
    # Environmental conditions
    temp_before: Decimal
    temp_after: Decimal  
    humidity_before: Decimal
    humidity_after: Decimal
    
    # Equipment details
    equipment_nomenclature: str
    equipment_make: str
    equipment_model: str
    equipment_serial: str
    equipment_range: str
    equipment_unit: str

class SeriesMeasurement(BaseModel):
    series_number: int  # I, II, III, IV
    measurements: List[float]  # 5 measurements per series
    
class ReproducibilityData(BaseModel):
    calibration_date: date
    set_torque: float
    series_measurements: List[SeriesMeasurement]  # 4 series
    
    @validator('series_measurements')
    def validate_series(cls, v):
        if len(v) != 4:
            raise ValueError('Exactly 4 series required for reproducibility test')
        return v

class PositionMeasurement(BaseModel):
    position: str  # "0°", "90°", "180°", "270°"
    measurements: List[float]  # 10 measurements per position
    
class OutputDriveData(BaseModel):
    calibration_date: date
    set_torque: float
    position_measurements: List[PositionMeasurement]  # 4 positions
    
    @validator('position_measurements')
    def validate_positions(cls, v):
        expected_positions = ["0°", "90°", "180°", "270°"]
        actual_positions = [p.position for p in v]
        if set(actual_positions) != set(expected_positions):
            raise ValueError(f'Must include all positions: {expected_positions}')
        return v

class LoadingPointData(BaseModel):
    calibration_date: date
    set_torque: float
    position_measurements: List[Dict]  # 2 positions: -10mm, +10mm
    
class MeasurementCreate(BaseModel):
    job_id: int
    measurement_type: str
    measurement_data: Any  # Flexible for different measurement types

class MeasurementResponse(BaseModel):
    id: int
    job_id: int
    measurement_type: str
    measurement_plan_name: Optional[str]
    calibration_date: date
    is_completed: bool
    pass_fail_status: Optional[str]
    
    # Summary statistics
    total_points: Optional[int]
    readings_per_point: Optional[int]
    
    class Config:
        from_attributes = True

class UncertaintyCalculationResponse(BaseModel):
    id: int
    measurement_id: int
    set_torque: Decimal
    
    # Uncertainty components
    uncertainty_pressure_gauge: Optional[Decimal]
    resolution_input_pressure: Optional[Decimal]
    uncertainty_standard: Optional[Decimal]
    uncertainty_resolution: Optional[Decimal]
    uncertainty_reproducibility: Optional[Decimal]
    uncertainty_output_drive: Optional[Decimal]
    uncertainty_interface: Optional[Decimal]
    uncertainty_loading_point: Optional[Decimal]
    uncertainty_repeatability: Optional[Decimal]
    
    # Results
    combined_uncertainty: Optional[Decimal]
    expanded_uncertainty_percent: Optional[Decimal]
    expanded_uncertainty_absolute: Optional[Decimal]
    coverage_factor: int
    
    class Config:
        from_attributes = True
