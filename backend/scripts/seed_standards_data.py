#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.equipment import EquipmentCategory, EquipmentType
from app.models.standards import Standard, StandardsSelectionRule
from datetime import date, timedelta
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_standards_data():
    """Seed database with standards and selection rules - FIXED VERSION"""
    
    db = SessionLocal()
    
    try:
        # 1. Seed Equipment Categories (if not exists)
        logger.info("🏗️ Seeding Equipment Categories...")
        categories = [
            {"name": "Torque", "description": "Torque measurement instruments"},
            {"name": "Pressure", "description": "Pressure measurement instruments"},
            {"name": "Electrical", "description": "Electrical measurement instruments"},
            {"name": "Dimensional", "description": "Dimensional measurement instruments"}
        ]
        
        category_map = {}
        for cat_data in categories:
            existing = db.query(EquipmentCategory).filter(
                EquipmentCategory.name == cat_data["name"]
            ).first()
            
            if not existing:
                category = EquipmentCategory(**cat_data)
                db.add(category)
                db.flush()
                category_map[cat_data["name"]] = category.id
                logger.info(f"  ✅ Created category: {cat_data['name']}")
            else:
                category_map[cat_data["name"]] = existing.id
                logger.info(f"  ⚡ Category exists: {cat_data['name']}")
        
        # 2. Seed Equipment Types
        logger.info("🔧 Seeding Equipment Types...")
        equipment_types = [
            {
                "category": "Torque",
                "nomenclature": "TORQUE WRENCH",
                "type_code": "TW_GENERIC",
                "unit": "Nm",
                "min_range": 1.0,
                "max_range": 5000.0,
                "classification": "Type I Class C",
                "calibration_method": "ISO 6789-1 & 2:2017"
            },
            {
                "category": "Torque", 
                "nomenclature": "HYDRAULIC TORQUE WRENCH",
                "type_code": "HTW_GENERIC",
                "unit": "Nm",
                "min_range": 100.0,
                "max_range": 50000.0,
                "classification": "Hydraulic",
                "calibration_method": "ISO 6789-1 & 2:2017"
            },
            {
                "category": "Pressure",
                "nomenclature": "PRESSURE GAUGE",
                "type_code": "PG_GENERIC",
                "unit": "bar",
                "min_range": 0.0,
                "max_range": 1000.0,
                "classification": "Digital",
                "calibration_method": "DKD-R-6-1"
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
                db.flush()
                equipment_type_map[eq_data["type_code"]] = equipment_type
                logger.info(f"  ✅ Created equipment type: {eq_data['type_code']}")
            else:
                equipment_type_map[eq_data["type_code"]] = existing
                logger.info(f"  ⚡ Equipment type exists: {eq_data['type_code']}")
        
        # 3. Seed Standards
        logger.info("📏 Seeding Standards...")
        standards_data = [
            {
                "nomenclature": "TORQUE TRANSDUCER ( 100 - 1500 Nm )",
                "manufacturer": "NORBAR, UK",
                "model_serial_no": "50676.LOG/169590/148577",
                "uncertainty": Decimal("0.0015"),
                "accuracy": "0.005",
                "resolution": Decimal("0.1"),
                "unit": "Nm",
                "range_min": Decimal("100"),
                "range_max": Decimal("1500"),
                "equipment_category_id": category_map["Torque"],
                "applicable_range_min": 100.0,
                "applicable_range_max": 1500.0,
                "discipline": "Torque",
                "certificate_no": "SCPL/CC/1289/07/2024-2025",
                "calibration_valid_upto": date(2026, 7, 25),
                "traceable_to_lab": "Traceable to NABL Accredited Lab No. CC 2874",
                "is_active": True,
                "is_expired": False
            },
            {
                "nomenclature": "TORQUE TRANSDUCER ( 1000 - 40000 Nm)",
                "manufacturer": "NORBAR, UK",
                "model_serial_no": "50781.LOG / 201062 / 148577",
                "uncertainty": Decimal("0.0016"),
                "accuracy": "0.005",
                "resolution": Decimal("1"),
                "unit": "Nm",
                "range_min": Decimal("1000"),
                "range_max": Decimal("40000"),
                "equipment_category_id": category_map["Torque"],
                "applicable_range_min": 1000.0,
                "applicable_range_max": 40000.0,
                "discipline": "Torque",
                "certificate_no": "SCPL/CC/3685/03/2023-2024",
                "calibration_valid_upto": date(2026, 3, 13),
                "traceable_to_lab": "Traceable to NABL Accredited Lab No. CC 2874",
                "is_active": True,
                "is_expired": False
            },
            {
                "nomenclature": "DIGITAL PRESSURE GAUGE 1000 BAR",
                "manufacturer": "MASS",
                "model_serial_no": "MG301/ 25.CJ.017",
                "uncertainty": Decimal("0.0039"),
                "accuracy": "± 0.25% FS",
                "resolution": Decimal("0.1"),
                "unit": "bar",
                "range_min": Decimal("0"),
                "range_max": Decimal("1000"),
                "equipment_category_id": category_map["Pressure"],
                "applicable_range_min": 0.0,
                "applicable_range_max": 1000.0,
                "discipline": "Pressure",
                "certificate_no": "NEPL / C / 2025 / 98-9",
                "calibration_valid_upto": date(2026, 3, 25),
                "traceable_to_lab": "Traceable to NABL Accredited Lab No. CC-3217",
                "is_active": True,
                "is_expired": False
            }
        ]
        
        standard_map = {}
        for std_data in standards_data:
            existing = db.query(Standard).filter(
                Standard.nomenclature == std_data["nomenclature"],
                Standard.model_serial_no == std_data["model_serial_no"]
            ).first()
            
            if not existing:
                standard = Standard(**std_data)
                db.add(standard)
                db.flush()
                standard_map[std_data["nomenclature"]] = standard
                logger.info(f"  ✅ Created standard: {std_data['nomenclature'][:30]}...")
            else:
                standard_map[std_data["nomenclature"]] = existing
                logger.info(f"  ⚡ Standard exists: {std_data['nomenclature'][:30]}...")
        
        # 4. Seed Selection Rules
        logger.info("🎯 Seeding Selection Rules...")
        selection_rules = [
            {
                "equipment_type_code": "TW_GENERIC",
                "standard_nomenclature": "TORQUE TRANSDUCER ( 100 - 1500 Nm )",
                "priority": 1,
                "range_min": 1.0,
                "range_max": 1500.0,
                "rule_name": "Small Torque Range Rule",
                "is_active": True
            },
            {
                "equipment_type_code": "HTW_GENERIC",
                "standard_nomenclature": "TORQUE TRANSDUCER ( 1000 - 40000 Nm)",
                "priority": 1,
                "range_min": 1000.0,
                "range_max": 40000.0,
                "rule_name": "Large Torque Range Rule",
                "is_active": True
            },
            {
                "equipment_type_code": "PG_GENERIC",
                "standard_nomenclature": "DIGITAL PRESSURE GAUGE 1000 BAR",
                "priority": 1,
                "range_min": 0.0,
                "range_max": 1000.0,
                "rule_name": "Pressure Gauge Rule",
                "is_active": True
            }
        ]
        
        for rule_data in selection_rules:
            equipment_type_code = rule_data["equipment_type_code"]
            standard_nomenclature = rule_data["standard_nomenclature"]
            
            if (equipment_type_code in equipment_type_map and 
                standard_nomenclature in standard_map):
                
                equipment_type = equipment_type_map[equipment_type_code]
                standard = standard_map[standard_nomenclature]
                
                # Check if rule already exists
                existing_rule = db.query(StandardsSelectionRule).filter(
                    StandardsSelectionRule.equipment_type_id == equipment_type.id,
                    StandardsSelectionRule.standard_id == standard.id
                ).first()
                
                if not existing_rule:
                    rule = StandardsSelectionRule(
                        equipment_type_id=equipment_type.id,
                        standard_id=standard.id,
                        priority=rule_data["priority"],
                        range_min=rule_data["range_min"],
                        range_max=rule_data["range_max"],
                        rule_name=rule_data["rule_name"],
                        is_active=rule_data["is_active"]
                    )
                    db.add(rule)
                    logger.info(f"  ✅ Created rule: {rule_data['rule_name']}")
                else:
                    logger.info(f"  ⚡ Rule exists: {rule_data['rule_name']}")
            else:
                logger.warning(f"  ⚠️ Skipping rule {rule_data['rule_name']} - missing dependencies")
        
        # Commit all changes
        db.commit()
        
        # Final summary
        logger.info("✅ Standards data seeded successfully!")
        logger.info(f"  - {len(categories)} categories")
        logger.info(f"  - {len(equipment_types)} equipment types")
        logger.info(f"  - {len(standards_data)} standards")
        logger.info(f"  - {len(selection_rules)} selection rules")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding standards data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_standards_data()
