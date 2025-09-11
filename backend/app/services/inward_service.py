from sqlalchemy.orm import Session
from app.models.inward import Inward
from app.models.jobs import Job
from app.models.srf import SRFItem
from app.schemas.inward import InwardCreate
from app.services.standards_selection_service import StandardsSelectionService
from app.crud.inward import InwardCrud
from datetime import date
import re
import logging

logger = logging.getLogger(__name__)

class InwardService:
    
    @staticmethod
    def create_inward_with_dynamic_job(
        db: Session,
        inward_data: InwardCreate,
        current_user: str = "system"
    ) -> Inward:
        """
        Create inward entry with dynamic job creation and standards selection
        """
        # Create inward entry using existing CRUD
        inward = InwardCrud.create_inward(db, inward_data, current_user)
        
        # If condition is satisfactory, create job with dynamic standards
        if inward.condition_on_receipt == 'satisfactory':
            try:
                job = InwardService._create_dynamic_job(db, inward, current_user)
                logger.info(f"Dynamic job {job.job_number} created for inward {inward.nepl_id}")
            except Exception as e:
                logger.error(f"Failed to create dynamic job for inward {inward.nepl_id}: {e}")
                # Fallback to basic job creation
                job = InwardService._create_basic_job(db, inward, current_user)
        
        return inward
    
    @staticmethod
    def _create_dynamic_job(db: Session, inward: Inward, current_user: str) -> Job:
        """
        Create job with dynamic standards selection
        """
        srf_item = inward.srf_item
        
        # Parse equipment range
        range_info = InwardService._parse_equipment_range(srf_item.range_text)
        
        # Generate job number
        job_number = f"JOB-{inward.nepl_id}"
        
        # Determine calibration type and method
        calibration_config = InwardService._determine_calibration_config(
            srf_item.equip_desc, range_info['min'], range_info['max'], srf_item.unit
        )
        
        # Create job
        db_job = Job(
            inward_id=inward.id,
            job_number=job_number,
            nepl_work_id=inward.nepl_id,
            calibration_type=calibration_config['type'],
            calibration_method=calibration_config['method'],
            measurement_points=calibration_config['measurement_points'],
            status="pending",
            created_by=current_user
        )
        
        db.add(db_job)
        db.flush()  # Get job ID
        
        # Auto-select standards
        try:
            selected_standards = StandardsSelectionService.auto_select_standards_for_job(
                db=db,
                job_id=db_job.id,
                equipment_desc=srf_item.equip_desc,
                range_min=range_info['min'],
                range_max=range_info['max'],
                unit=srf_item.unit or "Nm"
            )
            
            # Create job standards
            if selected_standards:
                StandardsSelectionService.create_job_standards(db, db_job.id, selected_standards)
                
                # Update job with standards summary
                standards_summary = [
                    std['standard'].nomenclature for std in selected_standards
                ]
                db_job.special_instructions = f"Auto-selected standards: {', '.join(standards_summary[:2])}"
            else:
                db_job.special_instructions = "No suitable standards found - manual selection required"
                
        except Exception as e:
            logger.error(f"Standards selection failed for job {db_job.id}: {e}")
            db_job.special_instructions = f"Standards selection error: {str(e)}"
        
        db.commit()
        db.refresh(db_job)
        
        return db_job
    
    @staticmethod
    def _create_basic_job(db: Session, inward: Inward, current_user: str) -> Job:
        """
        Fallback basic job creation
        """
        return InwardCrud.create_job_from_inward(db, inward.id, current_user)
    
    @staticmethod
    def _parse_equipment_range(range_text: str) -> dict:
        """
        Parse range text to extract min and max values
        """
        if not range_text:
            return {'min': 0, 'max': 1000}
        
        # Try to extract numbers from range text
        numbers = re.findall(r'\d+(?:\.\d+)?', range_text.replace(',', ''))
        
        if len(numbers) >= 2:
            return {
                'min': float(numbers[0]),
                'max': float(numbers[1])
            }
        elif len(numbers) == 1:
            return {
                'min': 0,
                'max': float(numbers[0])
            }
        else:
            return {'min': 0, 'max': 1000}
    
    @staticmethod
    def _determine_calibration_config(
        equip_desc: str,
        range_min: float,
        range_max: float,
        unit: str
    ) -> dict:
        """
        Determine calibration configuration based on equipment
        """
        equip_desc_upper = equip_desc.upper()
        
        if "TORQUE" in equip_desc_upper:
            return {
                'type': "Torque",
                'method': "ISO 6789-1 & 2:2017",
                'measurement_points': ["20%", "60%", "100%"]
            }
        elif "PRESSURE" in equip_desc_upper:
            return {
                'type': "Pressure",
                'method': "DKD-R-6-1",
                'measurement_points': ["0%", "25%", "50%", "75%", "100%"]
            }
        elif "EARTH" in equip_desc_upper or "TESTER" in equip_desc_upper:
            return {
                'type': "Electrical",
                'method': "IEC 61557",
                'measurement_points': ["10%", "50%", "90%"]
            }
        else:
            return {
                'type': "General",
                'method': "As per standard",
                'measurement_points': ["As per requirement"]
            }
    
    # Add the missing methods referenced in your existing code
    @staticmethod
    def _create_generic_job(db: Session, inward: Inward, current_user: str) -> Job:
        """Generic fallback job creation"""
        return InwardCrud.create_job_from_inward(db, inward.id, current_user)
