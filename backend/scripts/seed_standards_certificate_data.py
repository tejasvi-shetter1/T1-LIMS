# scripts/seed_standards_certificate_data.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.calculations import StandardsCertificateData
from datetime import date

def seed_norbar_40000_nm_certificate():
    """Seed NORBAR 40000 Nm certificate data"""
    db = SessionLocal()
    
    try:
        # NORBAR 40000 Nm certificate data
        certificate_data = {
            "standard_id": 1,  # Assuming this is TORQUE TRANSDUCER ( 1000 - 40000 Nm)
            "certificate_validity_start": date(2024, 3, 13),
            "certificate_validity_end": date(2026, 3, 13),
            "certificate_reference": "SCPL/CC/3685/03/2023-2024",
            "traceability_chain": "Traceable to NABL Accredited Lab No. CC 2874",
            "calibration_points": [
                {"applied_torque": 0, "indicated_torque": 0, "error": 0.0, "uncertainty": 0},
                {"applied_torque": 1000, "indicated_torque": 1001.0, "error": -1.0, "uncertainty": 0.16},
                {"applied_torque": 5000, "indicated_torque": 5000.0, "error": 0.0, "uncertainty": 0.07},
                {"applied_torque": 10000, "indicated_torque": 9997.0, "error": 3.0, "uncertainty": 0.05},
                {"applied_torque": 15000, "indicated_torque": 14992.7, "error": 7.3, "uncertainty": 0.04},
                {"applied_torque": 20000, "indicated_torque": 19989.0, "error": 11.0, "uncertainty": 0.04},
                {"applied_torque": 25000, "indicated_torque": 24984.7, "error": 15.3, "uncertainty": 0.04},
                {"applied_torque": 30000, "indicated_torque": 29980.7, "error": 19.3, "uncertainty": 0.04},
                {"applied_torque": 35000, "indicated_torque": 34978.3, "error": 21.7, "uncertainty": 0.04},
                {"applied_torque": 40000, "indicated_torque": 39976.7, "error": 23.3, "uncertainty": 0.04}
            ],
            "measurement_conditions": {
                "temperature": "23°C ± 2°C",
                "humidity": "60% ± 10%",
                "calibration_method": "ISO 6789"
            }
        }
        
        cert_data = StandardsCertificateData(**certificate_data)
        db.add(cert_data)
        
        print("✅ NORBAR 40000 Nm certificate data seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding NORBAR certificate: {e}")
    finally:
        db.close()

def seed_norbar_1500_nm_certificate():
    """Seed NORBAR 1500 Nm certificate data"""
    db = SessionLocal()
    
    try:
        certificate_data = {
            "standard_id": 2,  # Assuming this is TORQUE TRANSDUCER ( 100 - 1500 Nm )
            "certificate_validity_start": date(2024, 7, 25),
            "certificate_validity_end": date(2026, 7, 25),
            "certificate_reference": "SCPL/CC/1289/07/2024-2025",
            "traceability_chain": "Traceable to NABL Accredited Lab No. CC 2874",
            "calibration_points": [
                {"applied_torque": 0, "indicated_torque": 0.0, "error": 0.0, "uncertainty": 0},
                {"applied_torque": 100, "indicated_torque": 100.25, "error": -0.25, "uncertainty": 0.15},
                {"applied_torque": 150, "indicated_torque": 150.3, "error": -0.3, "uncertainty": 0.13},
                {"applied_torque": 300, "indicated_torque": 300.35, "error": -0.35, "uncertainty": 0.05},
                {"applied_torque": 450, "indicated_torque": 450.5, "error": -0.5, "uncertainty": 0.03},
                {"applied_torque": 600, "indicated_torque": 600.55, "error": -0.55, "uncertainty": 0.03},
                {"applied_torque": 750, "indicated_torque": 750.65, "error": -0.65, "uncertainty": 0.02},
                {"applied_torque": 900, "indicated_torque": 900.775, "error": -0.775, "uncertainty": 0.02},
                {"applied_torque": 1050, "indicated_torque": 1050.8, "error": -0.8, "uncertainty": 0.02},
                {"applied_torque": 1200, "indicated_torque": 1200.875, "error": -0.875, "uncertainty": 0.01},
                {"applied_torque": 1350, "indicated_torque": 1350.825, "error": -0.825, "uncertainty": 0.01},
                {"applied_torque": 1500, "indicated_torque": 1500.85, "error": -0.85, "uncertainty": 0.01}
            ],
            "measurement_conditions": {
                "temperature": "23°C ± 2°C", 
                "humidity": "60% ± 10%",
                "calibration_method": "ISO 6789"
            }
        }
        
        cert_data = StandardsCertificateData(**certificate_data)
        db.add(cert_data)
        
        print("✅ NORBAR 1500 Nm certificate data seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding NORBAR 1500 certificate: {e}")
    finally:
        db.close()

def seed_lorenz_5000_nm_certificate():
    """Seed Lorenz 5000 Nm certificate data"""
    db = SessionLocal()
    
    try:
        certificate_data = {
            "standard_id": 3,  # Assuming this is TORQUE TRANSDUCER ( 500 - 5000 Nm )
            "certificate_validity_start": date(2024, 6, 16),
            "certificate_validity_end": date(2026, 6, 16),
            "certificate_reference": "SCPL/CC/0854/06/2024-2025",
            "traceability_chain": "Traceable to NABL Accredited Lab No. CC 2874",
            "calibration_points": [
                {"applied_torque": 0, "indicated_torque": 0.0, "error": 0.0, "uncertainty": 0},
                {"applied_torque": 500, "indicated_torque": 500.7, "error": -0.7, "uncertainty": 0.29},
                {"applied_torque": 1000, "indicated_torque": 1002.0, "error": -2.0, "uncertainty": 0.13},
                {"applied_torque": 1500, "indicated_torque": 1503.3, "error": -3.3, "uncertainty": 0.11},
                {"applied_torque": 2000, "indicated_torque": 2004.3, "error": -4.3, "uncertainty": 0.08},
                {"applied_torque": 2500, "indicated_torque": 2505.7, "error": -5.7, "uncertainty": 0.06},
                {"applied_torque": 3000, "indicated_torque": 3007.0, "error": -7.0, "uncertainty": 0.04},
                {"applied_torque": 3500, "indicated_torque": 3508.3, "error": -8.3, "uncertainty": 0.05},
                {"applied_torque": 4000, "indicated_torque": 4010.3, "error": -10.3, "uncertainty": 0.03},
                {"applied_torque": 4500, "indicated_torque": 4512.3, "error": -12.3, "uncertainty": 0.02},
                {"applied_torque": 5000, "indicated_torque": 5014.0, "error": -14.0, "uncertainty": 0.01}
            ],
            "measurement_conditions": {
                "temperature": "23°C ± 2°C",
                "humidity": "60% ± 10%", 
                "calibration_method": "ISO 6789"
            }
        }
        
        cert_data = StandardsCertificateData(**certificate_data)
        db.add(cert_data)
        
        print("✅ Lorenz 5000 Nm certificate data seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding Lorenz certificate: {e}")
    finally:
        db.close()

def run_all_certificate_seeds():
    """Run all certificate seeding functions"""
    print("🌱 Starting standards certificate data seeding...")
    
    seed_norbar_40000_nm_certificate()
    seed_norbar_1500_nm_certificate() 
    seed_lorenz_5000_nm_certificate()
    
    print("✅ All standards certificate data seeded successfully!")

if __name__ == "__main__":
    run_all_certificate_seeds()
