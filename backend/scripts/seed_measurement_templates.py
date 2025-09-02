import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.measurements import MeasurementTemplate

def seed_measurement_templates():
    """Seed measurement templates based on Excel analysis"""
    db = SessionLocal()
    
    try:
        # Torque measurement template (from Excel Raw Data sheet)
        torque_template = {
            "template_name": "ISO 6789-1 Torque Calibration",
            "equipment_type": "torque",
            "calibration_method": "ISO 6789-1 & 2:2017",
            "measurement_points": ["20%", "60%", "100%"],  # Standard points
            "readings_per_point": 5,
            "required_measurements": [
                "repeatability",      # A. Repeatability  
                "reproducibility",    # B. Reproducibility
                "output_drive",       # C. Output drive geometric effect
                "drive_interface",    # D. Drive interface variation
                "loading_point"       # E. Loading point variation
            ],
            "environmental_limits": {
                "temperature": {"min": 20, "max": 26, "unit": "°C"},
                "humidity": {"min": 0.4, "max": 0.7, "unit": "RH"}
            },
            "formula_pack": {
                "uncertainty_calculation": "ISO_GUM_Type_A_B",
                "coverage_factor": 2,
                "confidence_level": 95
            }
        }
        
        existing = db.query(MeasurementTemplate).filter(
            MeasurementTemplate.template_name == torque_template["template_name"]
        ).first()
        
        if not existing:
            template = MeasurementTemplate(**torque_template)
            db.add(template)
        
        # Hydraulic torque template (specific for hydraulic wrenches)
        hydraulic_template = {
            "template_name": "Hydraulic Torque Wrench Calibration",
            "equipment_type": "torque",
            "calibration_method": "ISO 6789-1 & 2:2017",
            "measurement_points": ["20%", "60%", "100%"],
            "readings_per_point": 5,
            "required_measurements": [
                "repeatability",
                "reproducibility", 
                "output_drive",
                "drive_interface",
                "loading_point"
            ],
            "environmental_limits": {
                "temperature": {"min": 20, "max": 26, "unit": "°C"},
                "humidity": {"min": 0.4, "max": 0.7, "unit": "RH"}
            },
            "formula_pack": {
                "uncertainty_calculation": "hydraulic_torque_specific",
                "pressure_compensation": True,
                "coverage_factor": 2
            }
        }
        
        existing_hydraulic = db.query(MeasurementTemplate).filter(
            MeasurementTemplate.template_name == hydraulic_template["template_name"]
        ).first()
        
        if not existing_hydraulic:
            template = MeasurementTemplate(**hydraulic_template)
            db.add(template)
        
        db.commit()
        print("Measurement templates seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding measurement templates: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_measurement_templates()
