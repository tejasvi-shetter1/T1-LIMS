import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.customers import Customer
from app.models.standards import Standard
from datetime import date

def seed_sample_data():
    """Seed database with sample customers and standards from Excel"""
    db = SessionLocal()
    
    try:
        # Create sample customers
        sample_customers = [
            {
                "name": "ENVISION WIND POWER TECHNOLOGIES INDIA PVT LTD",
                "contact_person": "Mr Palanikumar",
                "email": "palanikumar.p@envision-energy.com",
                "phone": "7806816671",
                "address": "C/O FOURTH PARTNER - TUTICORIN",
                "is_active": True
            },
            {
                "name": "Sarvashree Calibration Pvt Ltd",
                "contact_person": "Lab Manager",
                "email": "info@sarvashree.com",
                "phone": "9876543210",
                "address": "Bangalore, Karnataka",
                "is_active": True
            }
        ]
        
        for customer_data in sample_customers:
            existing = db.query(Customer).filter(Customer.name == customer_data["name"]).first()
            if not existing:
                customer = Customer(**customer_data)
                db.add(customer)
        
        # Create standards from Excel Standards sheet
        sample_standards = [
            {
                "nomenclature": "DIGITAL PRESSURE GAUGE 1000 BAR",
                "manufacturer": "MASS",
                "model_serial_no": "MG301/ 25.CJ.017",
                "uncertainty": 0.0039,
                "accuracy": "± 0.25% FS",
                "resolution": 0.1,
                "unit": "bar",
                "range_min": 0,
                "range_max": 1000,
                "certificate_no": "NEPL / C / 2025 / 98-9",
                "calibration_valid_upto": date(2026, 3, 25),
                "traceable_to_lab": "Traceable to NABL Accredited Lab No. CC-3217"
            },
            {
                "nomenclature": "TORQUE TRANSDUCER ( 1000 - 40000 Nm)",
                "manufacturer": "NORBAR, UK",
                "model_serial_no": "50781.LOG / 201062 / 148577",
                "uncertainty": 0.0016,
                "accuracy": "0.005",
                "resolution": 1,
                "unit": "Nm",
                "range_min": 1000,
                "range_max": 40000,
                "certificate_no": "SCPL/CC/3685/03/2023-2024",
                "calibration_valid_upto": date(2026, 3, 13),
                "traceable_to_lab": "Traceable to NABL Accredited Lab No. CC 2874"
            },
            {
                "nomenclature": "TORQUE TRANSDUCER ( 100 - 1500 Nm )",
                "manufacturer": "NORBAR, UK", 
                "model_serial_no": "50676.LOG/169590/148577",
                "uncertainty": 0.0015,
                "accuracy": "0.005",
                "resolution": 0.1,
                "unit": "Nm",
                "range_min": 100,
                "range_max": 1500,
                "certificate_no": "SCPL/CC/1289/07/2024-2025",
                "calibration_valid_upto": date(2026, 7, 25),
                "traceable_to_lab": "Traceable to NABL Accredited Lab No. CC 2874"
            }
        ]
        
        for standard_data in sample_standards:
            existing = db.query(Standard).filter(
                Standard.nomenclature == standard_data["nomenclature"],
                Standard.model_serial_no == standard_data["model_serial_no"]
            ).first()
            if not existing:
                standard = Standard(**standard_data)
                db.add(standard)
        
        db.commit()
        print("Sample data seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
