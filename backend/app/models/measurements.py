from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON, Boolean
from sqlalchemy.types import DECIMAL as Decimal
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum

class MeasurementType(str, enum.Enum):
    REPEATABILITY = "repeatability"           # A. Repeatability (5 readings per point)
    REPRODUCIBILITY = "reproducibility"       # B. Reproducibility (4 sequences)
    OUTPUT_DRIVE = "output_drive"            # C. Geometric effect of output drive (4 positions)
    DRIVE_INTERFACE = "drive_interface"      # D. Variation due to drive interface (4 positions)
    LOADING_POINT = "loading_point"          # E. Variation due to loading point (2 positions)

class Measurement(Base, TimestampMixin, AuditMixin):
    __tablename__ = "measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Measurement Configuration
    measurement_type = Column(String(50), nullable=False)  # From MeasurementType enum
    measurement_plan_name = Column(String(255))           # Custom measurement plan
    
    # Test Conditions (from Raw Data sheet)
    calibration_date = Column(Date, nullable=False)
    technician = Column(String(255))
    
    # Environmental Conditions  
    temp_before = Column(Decimal(5, 2))      # 23.4°C
    temp_after = Column(Decimal(5, 2))       # 23.6°C
    humidity_before = Column(Decimal(5, 4))  # 0.605
    humidity_after = Column(Decimal(5, 4))   # 0.606
    
    # Measurement Data (JSON structure for flexibility)
    measurement_data = Column(JSON, nullable=False)  # Store all readings and calculations
    
    # Results Summary
    is_completed = Column(Boolean, default=False)
    pass_fail_status = Column(String(50))  # "pass", "fail", "deviation"
    deviation_notes = Column(Text)
    
    # Relationships
    job = relationship("Job", back_populates="measurements")
    calculations = relationship("UncertaintyCalculation", back_populates="measurement")

class UncertaintyCalculation(Base, TimestampMixin, AuditMixin):
    __tablename__ = "uncertainty_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))                    # Can be linked to job or measurement
    measurement_id = Column(Integer, ForeignKey("measurements.id"))    # Optional - for specific measurement
    
    # Calculation Input (from Excel Uncertainty sheet)
    set_torque = Column(Decimal(15, 4), nullable=False)               # Ts (1349, 4269, 7190)
    
    # Uncertainty Components (exact from Excel formulas)
    uncertainty_pressure_gauge = Column(Decimal(20, 15))             # δS un
    resolution_input_pressure = Column(Decimal(20, 15))             # δP Resolution
    uncertainty_standard = Column(Decimal(20, 15))                  # Wmd (Standard)
    uncertainty_resolution = Column(Decimal(20, 15))                # Wr (Resolution)
    uncertainty_reproducibility = Column(Decimal(20, 15))           # Wrep (Reproducibility)
    uncertainty_output_drive = Column(Decimal(20, 15))              # Wod (Output drive)
    uncertainty_interface = Column(Decimal(20, 15))                 # Wint (Interface)
    uncertainty_loading_point = Column(Decimal(20, 15))             # Wl (Loading Point)
    uncertainty_repeatability = Column(Decimal(20, 15))             # brep (Type A)
    
    # Combined Calculations
    combined_uncertainty = Column(Decimal(20, 15))                  # W (Combined)
    coverage_factor = Column(Integer, default=2)                    # k=2
    expanded_uncertainty_percent = Column(Decimal(20, 15))          # U (±) %
    expanded_uncertainty_absolute = Column(Decimal(20, 15))         # U (Nm)
    
    # Measurement Error Analysis
    mean_measurement_error = Column(Decimal(20, 15))                # Mean value of error
    max_calibration_device_error = Column(Decimal(20, 15))          # Max measurement error
    
    # CMC Calculation
    cmc_value = Column(Decimal(20, 15))                             # CMC calculation
    cmc_absolute = Column(Decimal(20, 15))                          # CMC ABS
    
    # Final Result
    measurement_uncertainty_interval = Column(Decimal(20, 15))      # Final uncertainty interval
    
    # Relationships  
    job = relationship("Job", back_populates="uncertainty_budgets")
    measurement = relationship("Measurement", back_populates="calculations")

class MeasurementTemplate(Base, TimestampMixin):
    __tablename__ = "measurement_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template Configuration
    template_name = Column(String(255), nullable=False)             # "Torque Wrench Standard", "Hydraulic Wrench Standard"
    equipment_type = Column(String(100), nullable=False)            # "torque", "pressure", "dimension"
    calibration_method = Column(String(255))                        # "ISO 6789-1 & 2:2017"
    
    # Measurement Plan Configuration (from Excel analysis)
    measurement_points = Column(JSON, nullable=False)               # ["20%", "60%", "100%"]
    readings_per_point = Column(Integer, default=5)                 # 5 readings per point
    
    # Test Configuration
    required_measurements = Column(JSON, nullable=False)             # Which measurement types are required
    environmental_limits = Column(JSON)                             # Temp/humidity limits
    
    # Formula Configuration (discipline-specific)
    formula_pack = Column(JSON)                                     # Calculation formulas for this type
    
    is_active = Column(Boolean, default=True)
