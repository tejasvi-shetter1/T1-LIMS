from sqlalchemy.orm import Session
from app.models.equipment import EquipmentCategory, EquipmentType, StandardsSelectionRule
from app.models.standards import Standard
from app.models.measurements import MeasurementTemplate
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

class EquipmentService:
    
    @staticmethod
    def auto_detect_equipment_type(
        db: Session, 
        nomenclature: str, 
        range_text: str = None,
        unit: str = None
    ) -> Optional[EquipmentType]:
        """
        Auto-detect equipment type based on nomenclature, range, and unit
        This replaces the hardcoded logic in InwardCrud.create_job_from_inward
        """
        try:
            # Clean nomenclature for matching
            clean_nomenclature = nomenclature.upper().strip()
            
            # Parse range if provided
            range_min, range_max = EquipmentService._parse_range(range_text) if range_text else (None, None)
            
            # Query equipment types with fuzzy matching
            query = db.query(EquipmentType).filter(EquipmentType.is_active == True)
            
            # First, try exact nomenclature matching
            for eq_type in query.all():
                if EquipmentService._matches_nomenclature(clean_nomenclature, eq_type.nomenclature):
                    # Check range compatibility
                    if EquipmentService._range_compatible(range_min, range_max, eq_type):
                        # Check unit compatibility
                        if not unit or unit.upper() == eq_type.unit.upper():
                            logger.info(f"Auto-detected equipment type: {eq_type.nomenclature}")
                            return eq_type
            
            logger.warning(f"No equipment type found for: {nomenclature}")
            return None
            
        except Exception as e:
            logger.error(f"Equipment type detection failed: {e}")
            return None
    
    @staticmethod
    def get_measurement_template(db: Session, equipment_type_id: int) -> Optional[MeasurementTemplate]:
        """Get measurement template for equipment type"""
        return db.query(MeasurementTemplate)\
            .filter(MeasurementTemplate.equipment_type_id == equipment_type_id)\
            .filter(MeasurementTemplate.is_active == True)\
            .first()
    
    @staticmethod
    def get_applicable_standards(
        db: Session, 
        equipment_type_id: int,
        measurement_range: tuple = None
    ) -> List[Dict]:
        """Get applicable standards for equipment type"""
        
        query = db.query(Standard, StandardsSelectionRule)\
            .join(StandardsSelectionRule, Standard.id == StandardsSelectionRule.standard_id)\
            .filter(StandardsSelectionRule.equipment_type_id == equipment_type_id)\
            .filter(StandardsSelectionRule.is_active == True)\
            .filter(Standard.is_active == True)\
            .order_by(StandardsSelectionRule.priority)
        
        # Add range filtering if provided
        if measurement_range:
            range_min, range_max = measurement_range
            query = query.filter(
                StandardsSelectionRule.range_min <= range_min,
                StandardsSelectionRule.range_max >= range_max
            )
        
        results = []
        for standard, rule in query.all():
            results.append({
                "id": standard.id,
                "name": standard.nomenclature,
                "manufacturer": standard.manufacturer,
                "model": standard.model_serial_no,
                "uncertainty": float(standard.uncertainty),
                "certificate_no": standard.certificate_no,
                "valid_until": standard.calibration_valid_upto,
                "traceability": standard.traceable_to_lab,
                "priority": rule.priority
            })
        
        return results
    
    @staticmethod
    def _matches_nomenclature(input_nomenclature: str, db_nomenclature: str) -> bool:
        """Check if nomenclatures match using fuzzy logic"""
        input_clean = input_nomenclature.upper().strip()
        db_clean = db_nomenclature.upper().strip()
        
        # Exact match
        if input_clean == db_clean:
            return True
        
        # Contains match
        if input_clean in db_clean or db_clean in input_clean:
            return True
        
        # Keyword matching for common patterns
        keywords = ["TORQUE", "PRESSURE", "DIGITAL", "VERNIER", "EARTH", "HYDRAULIC"]
        input_keywords = [kw for kw in keywords if kw in input_clean]
        db_keywords = [kw for kw in keywords if kw in db_clean]
        
        # If both have same keywords, likely a match
        return len(set(input_keywords).intersection(set(db_keywords))) > 0
    
    @staticmethod
    def _range_compatible(range_min: float, range_max: float, equipment_type: EquipmentType) -> bool:
        """Check if measurement range is compatible with equipment type range"""
        if not all([range_min, range_max, equipment_type.min_range, equipment_type.max_range]):
            return True  # If no range info, assume compatible
        
        # Equipment type should encompass the measurement range
        return (equipment_type.min_range <= range_min and 
                equipment_type.max_range >= range_max)
    
    @staticmethod
    def _parse_range(range_text: str) -> tuple:
        """Parse range string like '20-100 NM' to (20.0, 100.0)"""
        try:
            # Remove units and spaces
            clean_range = re.sub(r'[A-Za-z\s]', '', range_text)
            
            if '-' in clean_range:
                parts = clean_range.split('-')
                return float(parts[0]), float(parts[1])
            else:
                # Single value
                value = float(clean_range)
                return value, value
                
        except Exception as e:
            logger.warning(f"Could not parse range '{range_text}': {e}")
            return None, None
