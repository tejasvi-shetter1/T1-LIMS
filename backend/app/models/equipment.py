# app/models/equipment.py (CORRECTED VERSION)
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class EquipmentCategory(Base, TimestampMixin):
    __tablename__ = "equipment_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    equipment_types = relationship("EquipmentType", back_populates="category")
    calculation_formulas = relationship("CalculationFormula", back_populates="category")
    formula_templates = relationship("CalculationFormulaTemplate", back_populates="equipment_category")
class EquipmentType(Base, TimestampMixin):
    __tablename__ = "equipment_types"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    
    # Basic information
    nomenclature = Column(String(200), nullable=False)
    type_code = Column(String(50), nullable=False, unique=True)
    unit = Column(String(20), nullable=False)
    min_range = Column(Float)
    max_range = Column(Float)
    classification = Column(String(100))
    calibration_method = Column(String(200))
    is_active = Column(Boolean, default=True)
    
    # Enhanced fields for dynamic selection
    measurement_points = Column(JSON)
    required_standards_config = Column(JSON)
    
    # FIXED: Complete Relationships
    category = relationship("EquipmentCategory", back_populates="equipment_types")
    measurement_templates = relationship("MeasurementTemplate", back_populates="equipment_type")
    jobs = relationship("Job", back_populates="equipment_type")
    # Note: standards_rules is in standards.py, not here
    calculation_methods = relationship("CalculationMethod", back_populates="equipment_type")
    formula_lookups = relationship("FormulaLookupTable", back_populates="equipment_type")
    standards_rules = relationship("StandardsSelectionRule", back_populates="equipment_type")
class CalculationFormula(Base, TimestampMixin):
    __tablename__ = "calculation_formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    formula_name = Column(String(100), nullable=False)
    formula_type = Column(String(50))
    formula_expression = Column(Text)
    parameters = Column(JSON)
    version = Column(String(10), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("EquipmentCategory", back_populates="calculation_formulas")
    