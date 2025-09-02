from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.inward import Inward
from app.models.jobs import Job 
from app.models.srf import SRFItem
from app.schemas.inward import InwardCreate #, JobCreate
from datetime import date

class InwardCrud:
    
    @staticmethod
    def generate_nepl_id(db: Session) -> str:
        """Generate unique NEPL ID: Format YYXXX (25001, 25002, etc.)"""
        current_year = date.today().year % 100  # Get last 2 digits of year
        
        # Get the highest NEPL ID for current year
        last_inward = db.query(Inward)\
            .filter(Inward.nepl_id.like(f"{current_year}%"))\
            .order_by(Inward.nepl_id.desc())\
            .first()
        
        if last_inward:
            last_num = int(last_inward.nepl_id[2:])  # Extract number part
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{current_year}{next_num:03d}"  # Format: 25001, 25002, etc.
    
    @staticmethod
    def create_inward(db: Session, inward_data: InwardCreate, current_user: str = "system") -> Inward:
        """Create inward entry from SRF item"""
        
        # Generate NEPL ID
        nepl_id = InwardCrud.generate_nepl_id(db)
        
        # Create inward entry
        db_inward = Inward(
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
        
        db.add(db_inward)
        db.commit()
        db.refresh(db_inward)
        
        # Auto-create job if inward is satisfactory
        if db_inward.condition_on_receipt == 'satisfactory':
            InwardCrud.create_job_from_inward(db, db_inward.id, current_user)
        
        return db_inward
    
    @staticmethod
    def create_job_from_inward(db: Session, inward_id: int, current_user: str = "system") -> Job:
        """Auto-create job from inward entry"""
        
        inward = db.query(Inward).filter(Inward.id == inward_id).first()
        if not inward:
            raise ValueError("Inward entry not found")
        
        # Generate job number
        job_number = f"JOB-{inward.nepl_id}"
        
        # Determine calibration type from equipment description
        equip_desc = inward.srf_item.equip_desc.upper()
        if "TORQUE" in equip_desc:
            calibration_type = "Torque"
            calibration_method = "ISO 6789-1 & 2:2017"
            measurement_points = ["20%", "60%", "100%"]  # Standard torque points
        elif "PRESSURE" in equip_desc:
            calibration_type = "Pressure"
            calibration_method = "DKD-R-6-1"
            measurement_points = ["0%", "25%", "50%", "75%", "100%"]
        else:
            calibration_type = "General"
            calibration_method = "As per standard"
            measurement_points = ["As per requirement"]
        
        # Create job
        db_job = Job(
            inward_id=inward_id,
            job_number=job_number,
            nepl_work_id=inward.nepl_id,
            calibration_type=calibration_type,
            calibration_method=calibration_method,
            measurement_points=measurement_points,
            calibration_status="pending",
            created_by=current_user
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return db_job
    
    @staticmethod
    def get_inward_list(db: Session, skip: int = 0, limit: int = 100) -> List[Inward]:
        """Get paginated inward list with SRF details"""
        return db.query(Inward)\
            .join(SRFItem)\
            .order_by(Inward.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
