from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.srf import SRF, SRFItem
from app.models.customers import Customer
from app.schemas.srf import SRFCreate, SRFItemCreate, SRFUpdate
from datetime import date

class SRFCrud:
    
    @staticmethod
    def generate_srf_number() -> str:
        """Generate unique SRF number: NEPL-YYYY-MMDD-XXX"""
        today = date.today()
        base = f"NEPL-{today.year}-{today.strftime('%m%d')}"
        # Get the last SRF number for today to increment
        return f"{base}-001"  # Implement proper auto-increment logic
    
    @staticmethod
    def create_srf(db: Session, srf_data: SRFCreate, current_user: str = "system") -> SRF:
        """Create new SRF with items"""
        
        # Generate SRF number
        srf_no = SRFCrud.generate_srf_number()
        
        # Create SRF
        db_srf = SRF(
            srf_no=srf_no,
            customer_id=srf_data.customer_id,
            contact_person=srf_data.contact_person,
            date_received=srf_data.date_received or date.today(),
            priority=srf_data.priority,
            special_instructions=srf_data.special_instructions,
            nextage_contract_reference=srf_data.nextage_contract_reference,
            calibration_frequency=srf_data.calibration_frequency,
            created_by=current_user
        )
        
        db.add(db_srf)
        db.flush()  # Get the ID without committing
        
        # Create SRF Items
        for idx, item_data in enumerate(srf_data.items, 1):
            db_item = SRFItem(
                srf_id=db_srf.id,
                sl_no=idx,
                equip_desc=item_data.equip_desc,
                make=item_data.make,
                model=item_data.model,
                serial_no=item_data.serial_no,
                range_text=item_data.range_text,
                unit=item_data.unit,
                calibration_points=item_data.calibration_points,
                calibration_mode=item_data.calibration_mode,
                quantity=item_data.quantity,
                remarks=item_data.remarks
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_srf)
        return db_srf
    
    @staticmethod
    def get_srf_by_id(db: Session, srf_id: int) -> Optional[SRF]:
        """Get SRF by ID with all items"""
        return db.query(SRF).filter(SRF.id == srf_id).first()
    
    @staticmethod
    def get_srfs_list(db: Session, skip: int = 0, limit: int = 100) -> List[SRF]:
        """Get paginated list of SRFs"""
        return db.query(SRF)\
            .join(Customer)\
            .order_by(SRF.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def update_srf_status(db: Session, srf_id: int, new_status: str, current_user: str = "system") -> Optional[SRF]:
        """Update SRF status"""
        db_srf = db.query(SRF).filter(SRF.id == srf_id).first()
        if db_srf:
            db_srf.status = new_status
            db_srf.updated_by = current_user
            db.commit()
            db.refresh(db_srf)
        return db_srf
