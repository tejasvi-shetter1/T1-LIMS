from sqlalchemy.orm import Session
from app.models.inward import Inward
from app.models.jobs import Job
from app.models.srf import SRFItem
from app.services.equipment_service import EquipmentService
from app.schemas.inward import InwardCreate
from datetime import date
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
        Create inward entry and auto-generate job using DYNAMIC equipment logic
        This REPLACES the hardcoded logic in InwardCrud.create_job_from_inward
        """
        
        # Generate NEPL ID
        nepl_id = InwardService._generate_nepl_id(db)
        
        # Create inward entry
        inward = Inward(
            srf_item_id=inward_data.srf_item_id,
            nepl_id=nepl_id,
            inward_date=inward_data.inward_date or date.today(),
            customer_dc_no=inward_data.customer_dc_no,
            customer_dc_date=inward_data.customer_dc_date,
            condition_on_receipt=inward_data.condition_on_receipt,
            visual_inspection_notes=inward_data.visual_inspection_notes,
            received_by=inward_data.received_by or current_user,
            supplier=inward_data.supplier,
            quantity_received=inward_data.quantity_received,
            created_by=current_user
        )
        
        db.add(inward)
        db.flush()  # Get inward ID
        
        # Auto-create job if condition is satisfactory
        if inward.condition_on_receipt == 'satisfactory':
            job = InwardService._create_dynamic_job(db, inward, current_user)
            logger.info(f"  Job {job.job_number} created dynamically for {inward.nepl_id}")
        
        db.commit()
        db.refresh(inward)
        return inward
    
    @staticmethod
    def _create_dynamic_job(db: Session, inward: Inward, current_user: str) -> Job:
        """
        Create job using DYNAMIC equipment detection
        NO MORE HARDCODING!
        """
        
        # Get SRF item details
        srf_item = inward.srf_item
        
        # 🚀 DYNAMIC EQUIPMENT DETECTION
        equipment_type = EquipmentService.auto_detect_equipment_type(
            db=db,
            nomenclature=srf_item.equip_desc,
            range_text=srf_item.range_text,
            unit=srf_item.unit
        )
        
        if not equipment_type:
            logger.warning(f"⚠️ No equipment type detected, creating generic job")
            # Fallback to generic job
            return InwardService._create_generic_job(db, inward, current_user)
        
        # Get measurement template for this equipment type
        measurement_template = EquipmentService.get_measurement_template(db, equipment_type.id)
        
        # Get applicable standards
        range_min, range_max = EquipmentService._parse_range(srf_item.range_text) if srf_item.range_text else (None, None)
        applicable_standards = EquipmentService.get_applicable_standards(
            db, equipment_type.id, (range_min, range_max) if range_min else None
        )
        
        # Create job with DYNAMIC configuration
        job = Job(
            inward_id=inward.id,
            job_number=f"JOB-{inward.nepl_id}",
            nepl_work_id=inward.nepl_id,
            
            # DYNAMIC fields from equipment type
            equipment_type_id=equipment_type.id,
            calibration_type=equipment_type.category.name,
            calibration_method=equipment_type.calibration_method,
            
            # DYNAMIC measurement points from template
            measurement_points=measurement_template.measurement_points if measurement_template else ["As per requirement"],
            measurement_template_id=measurement_template.id if measurement_template else None,
            
            status="pending",
            created_by=current_user
        )
        
        db.add(job)
        db.flush()  # Get job ID
        
        # Link applicable standards to job
        from app.models.standards import JobStandard
        for standard_info in applicable_standards[:3]:  # Max 3 standards
            job_standard = JobStandard(
                job_id=job.id,
                standard_id=standard_info["id"],
                standard_sequence=standard_info["priority"],
                is_primary=(standard_info["priority"] == 1)
            )
            db.add(job_standard)
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Dynamic job created: {job.job_number} for {equipment_type.nomenclature}")
        return job
    
    @staticmethod
    def _create_generic_job(db: Session, inward: Inward, current_user: str) -> Job:
        """Fallback for unrecognized equipment"""
        job = Job(
            inward_id=inward.id,
            job_number=f"JOB-{inward.nepl_id}",
            nepl_work_id=inward.nepl_id,
            calibration_type="General",
            calibration_method="As per standard",
            measurement_points=["As per requirement"],
            status="pending",
            created_by=current_user
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def _generate_nepl_id(db: Session) -> str:
        """Generate unique NEPL ID"""
        current_year = date.today().year % 100
        
        last_inward = db.query(Inward)\
            .filter(Inward.nepl_id.like(f"{current_year}%"))\
            .order_by(Inward.nepl_id.desc())\
            .first()
        
        if last_inward:
            last_num = int(last_inward.nepl_id[2:])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{current_year}{next_num:03d}"
