# scripts/init_calculation_data.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.calculations import CalculationEngineConfig, FormulaLookupTable
from datetime import datetime

DATABASE_URL = "postgresql://postgres:Aimlsn%402025@localhost/nepl_lims_local"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initialize_calculation_data():
    """Initialize calculation engine with required data"""
    
    db = SessionLocal()
    try:
        print("🔧 Initializing Calculation Engine Data...")
        
        # 1. Create engine configuration
        config = CalculationEngineConfig(
            config_name="hydraulic_torque_wrench_standard",
            equipment_type="torque",
            stage1_methods={
                "repeatability": {"tolerance_limits": {"max_deviation_percent": 4.0}},
                "reproducibility": {},
                "output_drive": {},
                "interface": {},
                "loading_point": {}
            },
            stage2_methods={},
            stage3_methods={},
            tolerance_config={"uncertainty_max_percent": 3.0},
            auto_deviation_enabled=True,
            is_active=True
        )
        
        # Check if exists
        existing_config = db.query(CalculationEngineConfig).filter(
            CalculationEngineConfig.config_name == "hydraulic_torque_wrench_standard"
        ).first()
        
        if not existing_config:
            db.add(config)
            print("✅ Created calculation engine configuration")
        else:
            print("ℹ️ Configuration already exists")
        
        # 2. Create interpolation lookup table
        interpolation_table = FormulaLookupTable(
            table_name="torque_interpolation",
            lookup_type="interpolation",
            category="torque_transducer",
            data_structure={"columns": ["torque_value", "interpolation_error"]},
            lookup_data=[
                {"torque_value": 1225.0, "interpolation_error": 1.458},
                {"torque_value": 3602.8, "interpolation_error": 0.399},
                {"torque_value": 6352.8, "interpolation_error": 0.812}
            ],
            validity_period="permanent",
            is_active=True
        )
        
        existing_lookup = db.query(FormulaLookupTable).filter(
            FormulaLookupTable.table_name == "torque_interpolation"
        ).first()
        
        if not existing_lookup:
            db.add(interpolation_table)
            print("✅ Created interpolation lookup table")
        else:
            print("ℹ️ Lookup table already exists")
        
        db.commit()
        print("🎉 Calculation engine data initialized successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to initialize data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    initialize_calculation_data()
