from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin

class EquipmentCategory(Base, TimestampMixin):
    __tablename__ = "equipment_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # "Torque", "Pressure", "Electrical"
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    equipment_types = relationship("EquipmentType", back_populates="category")
    calculation_formulas = relationship("CalculationFormula", back_populates="category")

class EquipmentType(Base, TimestampMixin):
    __tablename__ = "equipment_types"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    nomenclature = Column(String(200), nullable=False)  # "TORQUE WRENCH 20-100NM"
    type_code = Column(String(50), nullable=False, unique=True)  # "TW_20_100"
    unit = Column(String(20), nullable=False)  # "Nm"
    min_range = Column(Float)
    max_range = Column(Float)
    classification = Column(String(100))  # "Type I Class C"
    calibration_method = Column(String(200))  # "ISO 6789-1 & 2 (2018)"
    is_active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("EquipmentCategory", back_populates="equipment_types")
    measurement_templates = relationship("MeasurementTemplate", back_populates="equipment_type")
    standards_rules = relationship("StandardsSelectionRule", back_populates="equipment_type")
    jobs = relationship("Job", back_populates="equipment_type")

class StandardsSelectionRule(Base, TimestampMixin):
    __tablename__ = "standards_selection_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"))
    standard_id = Column(Integer, ForeignKey("standards.id"))
    priority = Column(Integer, default=1)  # 1=primary, 2=secondary
    range_min = Column(Float)
    range_max = Column(Float)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    equipment_type = relationship("EquipmentType", back_populates="standards_rules")
    standard = relationship("Standard", back_populates="selection_rules")

class CalculationFormula(Base, TimestampMixin):
    __tablename__ = "calculation_formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    formula_name = Column(String(100), nullable=False)
    formula_type = Column(String(50))  # "uncertainty", "repeatability", "error"
    formula_expression = Column(Text)  # Python code or mathematical expression
    parameters = Column(JSON)  # Required parameters
    version = Column(String(10), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Relationships
    category = relationship("EquipmentCategory", back_populates="calculation_formulas")
