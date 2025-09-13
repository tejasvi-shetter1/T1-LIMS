# scripts/run_phase1_migration.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal
from seed_formula_lookup_tables import run_all_seeds
from seed_standards_certificate_data import run_all_certificate_seeds

def run_sql_migration(db, sql_file_path):
    """Execute SQL migration file"""
    try:
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = sql_content.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                db.execute(text(statement))
        
        db.commit()
        print(f"✅ Migration executed: {sql_file_path}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {sql_file_path} - {e}")
        raise

def run_phase1_migration():
    """Execute complete Phase 1 migration"""
    db = SessionLocal()
    
    try:
        print("🚀 Starting Phase 1: Database Schema Enhancement")
        print("=" * 60)
        
        # Step 1: Create new tables
        print("📋 Step 1: Creating new calculation engine tables...")
        run_sql_migration(db, "app/migrations/001_add_calculation_engine_tables.sql")
        
        # Step 2: Enhance existing tables
        print("📋 Step 2: Enhancing existing tables...")
        run_sql_migration(db, "app/migrations/002_enhance_existing_tables.sql")
        
        # Step 3: Seed formula lookup tables
        print("📋 Step 3: Seeding formula lookup tables...")
        run_all_seeds()
        
        # Step 4: Seed standards certificate data
        print("📋 Step 4: Seeding standards certificate data...")
        run_all_certificate_seeds()
        
        print("=" * 60)
        print("✅ Phase 1 Migration Completed Successfully!")
        print("\nNext Steps:")
        print("1. Update your models/__init__.py to include new models")
        print("2. Test database connections")
        print("3. Proceed to Phase 2: Core Calculation Engine")
        
    except Exception as e:
        print(f"❌ Phase 1 Migration Failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_phase1_migration()
