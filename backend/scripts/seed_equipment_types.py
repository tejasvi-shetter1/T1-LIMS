import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.equipment import EquipmentCategory, EquipmentType, StandardsSelectionRule
from app.models.measurements import MeasurementTemplate
from app.models.standards import Standard
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_equipment_data():
    """Seed equipment types, categories, and templates from SRF data"""
    db = SessionLocal()
    
    try:
        # 1. Seed Equipment Categories FIRST
        logger.info("🏗️ Seeding Equipment Categories...")
        categories = [
            {"name": "Torque", "description": "Torque measurement instruments"},
            {"name": "Pressure", "description": "Pressure measurement instruments"},
            {"name": "Electrical", "description": "Electrical measurement instruments"},
            {"name": "Dimensional", "description": "Dimensional measurement instruments"},
            {"name": "Flow", "description": "Flow measurement instruments"}
        ]
        
        category_map = {}
        for cat_data in categories:
            existing = db.query(EquipmentCategory).filter(
                EquipmentCategory.name == cat_data["name"]
            ).first()
            
            if not existing:
                category = EquipmentCategory(**cat_data)
                db.add(category)
                db.flush()  # Get ID without committing
                category_map[cat_data["name"]] = category.id
                logger.info(f"     Created category: {cat_data['name']}")
            else:
                category_map[cat_data["name"]] = existing.id
                logger.info(f"   ⚡ Category exists: {cat_data['name']}")
        
        db.commit()
        
        # 2. Seed Equipment Types SECOND
        logger.info("🔧 Seeding Equipment Types...")
        equipment_types = [
            # Torque Equipment (from SRF PDF)
            {
                "category": "Torque",
                "nomenclature": "TORQUE WRENCH 20-100NM",
                "type_code": "TW_20_100",
                "unit": "Nm",
                "min_range": 20.0,
                "max_range": 100.0,
                "classification": "Type I Class C",
                "calibration_method": "ISO 6789-1 & 2 (2018)"
            },
            {
                "category": "Torque",
                "nomenclature": "TORQUE WRENCH 60-340NM",
                "type_code": "TW_60_340",
                "unit": "Nm",
                "min_range": 60.0,
                "max_range": 340.0,
                "classification": "Type I Class C",
                "calibration_method": "ISO 6789-1 & 2 (2018)"
            },
            {
                "category": "Torque",
                "nomenclature": "PRIMO SQUARE DRIVE HYDRAULIC WRENCH",
                "type_code": "HW_PRIMO",
                "unit": "Nm",
                "min_range": 425.0,
                "max_range": 15000.0,
                "classification": "Indicating",
                "calibration_method": "ISO 6789-1 & 2 (2018)"
            },
            {
                "category": "Torque",
                "nomenclature": "TORQUE MULTIPLIER",
                "type_code": "TM_GENERIC",
                "unit": "Nm",
                "min_range": 1500.0,
                "max_range": 1500.0,
                "classification": "Multiplier",
                "calibration_method": "ISO 6789-1 & 2 (2018)"
            },
            
            # Pressure Equipment
            {
                "category": "Pressure",
                "nomenclature": "PRIMO STRECHER PUMP PRESSURE GAUGE",
                "type_code": "PSP_GAUGE",
                "unit": "MPa",
                "min_range": 0.0,
                "max_range": 100.0,
                "classification": "Digital Gauge",
                "calibration_method": "DKD-R-6-1"
            },
            
            # Electrical Equipment
            {
                "category": "Electrical",
                "nomenclature": "DIGITAL EARTH TESTER",
                "type_code": "DET_GENERIC",
                "unit": "ohms",
                "min_range": 0.0,
                "max_range": 1000.0,
                "classification": "Digital Tester",
                "calibration_method": "IEC 61557"
            },
            {
                "category": "Electrical",
                "nomenclature": "PHASE SEQUENCE METER",
                "type_code": "PSM_600V",
                "unit": "V",
                "min_range": 0.0,
                "max_range": 600.0,
                "classification": "Digital Meter",
                "calibration_method": "IEC 61010"
            },
            
            # Dimensional Equipment
            {
                "category": "Dimensional",
                "nomenclature": "DIGITAL VERNIER CALIPER",
                "type_code": "DVC_GENERIC",
                "unit": "mm",
                "min_range": 0.0,
                "max_range": 300.0,
                "classification": "Digital Caliper",
                "calibration_method": "ISO 13385"
            },
            
            # Flow Equipment
            {
                "category": "Flow",
                "nomenclature": "DIGITAL ANEMOMETER",
                "type_code": "DA_GENERIC",
                "unit": "m/s",
                "min_range": 0.4,
                "max_range": 30.0,
                "classification": "Digital Anemometer",
                "calibration_method": "ISO 3966"
            }
        ]
        
        equipment_type_map = {}
        for eq_data in equipment_types:
            existing = db.query(EquipmentType).filter(
                EquipmentType.type_code == eq_data["type_code"]
            ).first()
            
            if not existing:
                equipment_type = EquipmentType(
                    category_id=category_map[eq_data["category"]],
                    nomenclature=eq_data["nomenclature"],
                    type_code=eq_data["type_code"],
                    unit=eq_data["unit"],
                    min_range=eq_data["min_range"],
                    max_range=eq_data["max_range"],
                    classification=eq_data["classification"],
                    calibration_method=eq_data["calibration_method"]
                )
                db.add(equipment_type)
                db.flush()  # Get ID without committing
                equipment_type_map[eq_data["type_code"]] = equipment_type
                logger.info(f"    Created equipment type: {eq_data['type_code']}")
            else:
                equipment_type_map[eq_data["type_code"]] = existing
                logger.info(f"   ⚡ Equipment type exists: {eq_data['type_code']}")
        
        db.commit()
        
        # 3. CRITICAL FIX: Seed Measurement Templates with PROPER equipment_type_id
        logger.info(" Seeding Measurement Templates...")
        templates = [
            {
                "equipment_type_code": "TW_20_100",
                "template_name": "Standard Torque Wrench Template",
                "measurement_points": [20, 60, 100],  # Percentage
                "readings_per_point": 5,
                "required_measurements": ["repeatability", "reproducibility"],
                "environmental_limits": {"temp_range": [18, 28], "humidity_max": 80}
            },
            {
                "equipment_type_code": "HW_PRIMO",
                "template_name": "Hydraulic Wrench Template",
                "measurement_points": [1349, 4269, 7190],  # Absolute values from Excel
                "readings_per_point": 5,
                "required_measurements": ["repeatability", "reproducibility", "geometric_effects", "loading_point"],
                "environmental_limits": {"temp_range": [20, 30], "humidity_max": 70}
            },
            {
                "equipment_type_code": "DET_GENERIC",
                "template_name": "Digital Earth Tester Template",
                "measurement_points": [10, 50, 90],  # Percentage
                "readings_per_point": 3,
                "required_measurements": ["repeatability"],
                "environmental_limits": {"temp_range": [15, 35], "humidity_max": 85}
            }
        ]
        
        for template_data in templates:
            equipment_type_code = template_data["equipment_type_code"]
            
            if equipment_type_code in equipment_type_map:
                equipment_type = equipment_type_map[equipment_type_code]
                
                existing_template = db.query(MeasurementTemplate).filter(
                    MeasurementTemplate.equipment_type_id == equipment_type.id
                ).first()
                
                if not existing_template:
                    #  CRITICAL FIX: Use equipment_type_id instead of equipment_type string
                    template = MeasurementTemplate(
                        equipment_type_id=equipment_type.id,  #  FIXED: Use ID, not string
                        template_name=template_data["template_name"],
                        measurement_points=template_data["measurement_points"],
                        readings_per_point=template_data["readings_per_point"],
                        required_measurements=template_data["required_measurements"],
                        environmental_limits=template_data["environmental_limits"],
                        is_active=True
                    )
                    db.add(template)
                    logger.info(f"   Created template: {template_data['template_name']}")
                else:
                    logger.info(f"   Template exists: {template_data['template_name']}")
            else:
                logger.warning(f"   Equipment type not found: {equipment_type_code}")
        
        db.commit()
        
        logger.info(" Equipment data seeded successfully!")
        logger.info(f"   - {len(categories)} categories")
        logger.info(f"   - {len(equipment_types)} equipment types")
        logger.info(f"   - {len(templates)} measurement templates")
        
    except Exception as e:
        db.rollback()
        logger.error(f" Error seeding equipment data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_equipment_data()
