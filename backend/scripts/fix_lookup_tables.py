# scripts/fix_lookup_tables.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.calculations import FormulaLookupTable, CalculationEngineConfig
import json
from datetime import datetime

def clear_and_reseed_all_tables():
    """Clear existing tables and reseed with correct structure"""
    db = SessionLocal()
    
    try:
        # Clear all existing lookup tables
        print("🧹 Clearing existing lookup tables...")
        db.query(FormulaLookupTable).delete()
        db.commit()
        
        # 1. Seed Interpolation Table
        print("📊 Seeding interpolation lookup table...")
        interpolation_data = {
            "table_name": "torque_interpolation_1500_40000",
            "equipment_type_id": 1,
            "lookup_type": "interpolation",
            "category": "torque_transducer",
            "range_column": "torque_value",
            "validity_period": "23-11-2024 / 13-03-2026",
            "data_structure": {
                "format": "list_of_dicts",
                "columns": ["torque_value", "interpolation_error", "lower_range", "higher_range"]
            },
            "lookup_data": [
                {"torque_value": 1225.0, "interpolation_error": 1.458333333333333, "lower_range": 900.0, "higher_range": 1500.0},
                {"torque_value": 3602.8, "interpolation_error": 0.3992, "lower_range": 1500.0, "higher_range": 5000.0},
                {"torque_value": 6352.8, "interpolation_error": 0.81168, "lower_range": 5000.0, "higher_range": 10000.0}
            ]
        }
        
        interp_table = FormulaLookupTable(**interpolation_data)
        db.add(interp_table)
        
        # 2. Seed Master Transducer Uncertainty Table
        print("🎯 Seeding master transducer uncertainty table...")
        uncertainty_data = {
            "table_name": "master_transducer_uncertainty",
            "equipment_type_id": 1,
            "lookup_type": "uncertainty",
            "category": "master_standard",
            "range_column": "set_torque",
            "data_structure": {
                "format": "list_of_dicts",
                "columns": ["set_torque", "uncertainty", "uncertainty_half"]
            },
            "lookup_data": [
                {"set_torque": 1349.0, "uncertainty": 0.16, "uncertainty_half": 0.08},
                {"set_torque": 4269.0, "uncertainty": 0.05, "uncertainty_half": 0.025},
                {"set_torque": 7190.0, "uncertainty": 0.04, "uncertainty_half": 0.02}
            ]
        }
        
        uncertainty_table = FormulaLookupTable(**uncertainty_data)
        db.add(uncertainty_table)
        
        # 3. Seed CMC Lookup Table
        print("📋 Seeding CMC lookup table...")
        cmc_data = {
            "table_name": "cmc_scope_hydraulic",
            "equipment_type_id": 1,
            "lookup_type": "cmc",
            "category": "calibration_capability",
            "range_column": "torque_point",
            "data_structure": {
                "format": "list_of_dicts",
                "columns": ["lower_range", "higher_range", "cmc_percent"]
            },
            "lookup_data": [
                {"lower_range": 200, "higher_range": 1500, "cmc_percent": 0.58},
                {"lower_range": 1500, "higher_range": 5000, "cmc_percent": 0.37},
                {"lower_range": 5000, "higher_range": 10000, "cmc_percent": 0.49},
                {"lower_range": 10000, "higher_range": 20000, "cmc_percent": 0.52},
                {"lower_range": 20000, "higher_range": 35000, "cmc_percent": 0.53}
            ]
        }
        
        cmc_table = FormulaLookupTable(**cmc_data)
        db.add(cmc_table)
        
        # 4. Seed Measurement Error Table
        print("⚠️ Seeding measurement error table...")
        measurement_error_data = {
            "table_name": "measurement_error_calibration_device",
            "equipment_type_id": 1,
            "lookup_type": "measurement_error",
            "category": "device_error",
            "range_column": "torque_point",
            "data_structure": {
                "format": "list_of_dicts",
                "columns": ["range_min", "range_max", "error_percent"]
            },
            "lookup_data": [
                {"range_min": 100, "range_max": 1500, "error_percent": 0.15},
                {"range_min": 1501, "range_max": 35000, "error_percent": 0.16}
            ]
        }
        
        measurement_error_table = FormulaLookupTable(**measurement_error_data)
        db.add(measurement_error_table)
        
        # 5. Seed Pressure Gauge Uncertainty Table
        print("🔧 Seeding pressure gauge uncertainty table...")
        pressure_data = {
            "table_name": "pressure_gauge_mass_0_1000_bar",
            "equipment_type_id": 1,
            "lookup_type": "pressure_uncertainty",
            "category": "pressure_gauge",
            "range_column": "set_pressure",
            "validity_period": "Certificate Validity: MASS 0-1000 bar",
            "data_structure": {
                "format": "list_of_dicts",
                "columns": ["uncertainty_percent", "set_pressure_low", "set_pressure_high"]
            },
            "lookup_data": [
                {"uncertainty_percent": 0.39, "set_pressure_low": 70, "set_pressure_high": 138},
                {"uncertainty_percent": 0.39, "set_pressure_low": 210, "set_pressure_high": 276},
                {"uncertainty_percent": 0.39, "set_pressure_low": 420, "set_pressure_high": 414},
                {"uncertainty_percent": 0.39, "set_pressure_low": 560, "set_pressure_high": 552},
                {"uncertainty_percent": 0.39, "set_pressure_low": 700, "set_pressure_high": 690}
            ]
        }
        
        pressure_table = FormulaLookupTable(**pressure_data)
        db.add(pressure_table)
        
        # Commit all changes
        db.commit()
        print("✅ All lookup tables seeded successfully!")
        
        # Verify the data
        print("\n🔍 Verifying seeded data...")
        tables = db.query(FormulaLookupTable).all()
        for table in tables:
            print(f"  ✅ {table.table_name} ({table.lookup_type}/{table.category})")
            if isinstance(table.lookup_data, list):
                print(f"     Data entries: {len(table.lookup_data)}")
            else:
                print(f"     Data type: {type(table.lookup_data)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding tables: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clear_and_reseed_all_tables()