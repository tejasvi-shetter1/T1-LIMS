# scripts/check_lookup_tables.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.calculations import FormulaLookupTable
import json

# Database setup
DATABASE_URL = "postgresql://postgres:Aimlsn%402025@localhost/nepl_lims_local"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_lookup_tables():
    """Check what lookup tables exist in the database"""
    db = SessionLocal()
    
    try:
        tables = db.query(FormulaLookupTable).all()
        print(f"Found {len(tables)} lookup tables in database:")
        
        for table in tables:
            print(f"\n📋 Table: {table.table_name}")
            print(f"   Type: {table.lookup_type}")
            print(f"   Category: {table.category}")
            print(f"   Active: {table.is_active}")
            
            # Check lookup_data structure
            if table.lookup_data:
                if isinstance(table.lookup_data, str):
                    try:
                        data = json.loads(table.lookup_data)
                        print(f"   Data Type: {type(data)}")
                        if isinstance(data, list):
                            print(f"   Data Length: {len(data)}")
                            if data:
                                print(f"   First Item Keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                        elif isinstance(data, dict):
                            print(f"   Data Keys: {list(data.keys())}")
                    except json.JSONDecodeError:
                        print(f"   Data: Invalid JSON")
                else:
                    print(f"   Data Type: {type(table.lookup_data)}")
                    if isinstance(table.lookup_data, list):
                        print(f"   Data Length: {len(table.lookup_data)}")
                    elif isinstance(table.lookup_data, dict):
                        print(f"   Data Keys: {list(table.lookup_data.keys())}")
            else:
                print(f"   Data: None/Empty")
        
        # Test specific lookups
        print("\n🔍 Testing specific lookups:")
        
        # Test interpolation lookup
        interp_table = db.query(FormulaLookupTable).filter(
            FormulaLookupTable.lookup_type == "interpolation",
            FormulaLookupTable.category == "torque_transducer",
            FormulaLookupTable.is_active == True
        ).first()
        
        if interp_table:
            print(f"✅ Found interpolation table: {interp_table.table_name}")
            print(f"   Lookup data type: {type(interp_table.lookup_data)}")
        else:
            print("❌ No interpolation table found")
        
        # Test uncertainty lookup
        uncertainty_table = db.query(FormulaLookupTable).filter(
            FormulaLookupTable.lookup_type == "uncertainty",
            FormulaLookupTable.category == "master_standard",
            FormulaLookupTable.is_active == True
        ).first()
        
        if uncertainty_table:
            print(f"✅ Found uncertainty table: {uncertainty_table.table_name}")
            print(f"   Lookup data type: {type(uncertainty_table.lookup_data)}")
        else:
            print("❌ No uncertainty table found")
        
        # Test CMC lookup
        cmc_table = db.query(FormulaLookupTable).filter(
            FormulaLookupTable.lookup_type == "cmc",
            FormulaLookupTable.category == "calibration_capability",
            FormulaLookupTable.is_active == True
        ).first()
        
        if cmc_table:
            print(f"✅ Found CMC table: {cmc_table.table_name}")
            print(f"   Lookup data type: {type(cmc_table.lookup_data)}")
        else:
            print("❌ No CMC table found")
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_lookup_tables()