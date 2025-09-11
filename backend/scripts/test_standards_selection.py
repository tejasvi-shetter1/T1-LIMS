#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.standards_selection_service import StandardsSelectionService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_standards_selection():
    """Test standards auto-selection functionality"""
    
    db = SessionLocal()
    
    try:
        logger.info("🧪 Testing Standards Auto-Selection...")
        
        # Test Case 1: Torque Wrench
        logger.info("\n📋 Test Case 1: TORQUE WRENCH 20-100NM")
        selected = StandardsSelectionService.auto_select_standards_for_job(
            db=db,
            job_id=0,
            equipment_desc="TORQUE WRENCH 20-100NM",
            range_min=20.0,
            range_max=100.0,
            unit="Nm"
        )
        
        if selected:
            for std in selected:
                logger.info(f"  ✅ Selected: {std['standard'].nomenclature}")
                logger.info(f"     Reason: {std['selection_reason']}")
        else:
            logger.warning("  ❌ No standards selected")
        
        # Test Case 2: Hydraulic Wrench
        logger.info("\n📋 Test Case 2: HYDRAULIC TORQUE WRENCH 1000-15000NM")
        selected = StandardsSelectionService.auto_select_standards_for_job(
            db=db,
            job_id=0,
            equipment_desc="HYDRAULIC TORQUE WRENCH",
            range_min=1000.0,
            range_max=15000.0,
            unit="Nm"
        )
        
        if selected:
            for std in selected:
                logger.info(f"  ✅ Selected: {std['standard'].nomenclature}")
                logger.info(f"     Reason: {std['selection_reason']}")
        else:
            logger.warning("  ❌ No standards selected")
        
        # Test Case 3: Pressure Gauge
        logger.info("\n📋 Test Case 3: PRESSURE GAUGE 0-1000 BAR")
        selected = StandardsSelectionService.auto_select_standards_for_job(
            db=db,
            job_id=0,
            equipment_desc="PRESSURE GAUGE",
            range_min=0.0,
            range_max=1000.0,
            unit="bar"
        )
        
        if selected:
            for std in selected:
                logger.info(f"  ✅ Selected: {std['standard'].nomenclature}")
                logger.info(f"     Reason: {std['selection_reason']}")
        else:
            logger.warning("  ❌ No standards selected")
        
        logger.info("\n🎉 Testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Error in testing: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_standards_selection()
