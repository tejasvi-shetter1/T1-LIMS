from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models.srf import SRF, SRFItem
from app.models.customers import Customer
from app.schemas.srf import SRFCreate, SRFItemCreate, SRFUpdate
from datetime import date
from fastapi import HTTPException

class SRFCrud:
    
    @staticmethod
    def generate_srf_number(db: Session) -> str:
        """Generate unique SRF number: NEPL-YYYY-MMDD-XXX"""
        today = date.today()
        base = f"NEPL-{today.year}-{today.strftime('%m%d')}"
        
        # Get all existing SRF numbers for today
        existing_numbers = db.query(SRF.srf_no).filter(
            SRF.srf_no.like(f"{base}%")
        ).all()
        
        # Extract numeric suffixes and find the highest
        numbers = []
        for (srf_no,) in existing_numbers:
            try:
                number_part = srf_no.rsplit('-', 1)[-1]
                if number_part.isdigit():
                    numbers.append(int(number_part))
            except Exception:
                continue
        
        # Generate next number
        next_number = max(numbers, default=0) + 1
        return f"{base}-{next_number:03d}"
    
    @staticmethod
    def create_srf(db: Session, srf_data: SRFCreate, current_user: str = "system") -> SRF:
        """Create new SRF with items and retry logic for unique numbers"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Generate unique SRF number
                srf_no = SRFCrud.generate_srf_number(db)
                
                # Create SRF
                db_srf = SRF(
                    srf_no=srf_no,
                    customer_id=srf_data.customer_id,
                    contact_person=srf_data.contact_person,
                    date_received=srf_data.date_received or date.today(),
                    status="submitted",  #  Use lowercase to match enum
                    priority=srf_data.priority,
                    special_instructions=srf_data.special_instructions,
                    nextage_contract_reference=srf_data.nextage_contract_reference,
                    calibration_frequency=srf_data.calibration_frequency,
                    created_by=current_user
                )
                
                db.add(db_srf)
                db.flush()  # Get the ID without committing
                
                # Create SRF Items array
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
                
                # Commit all changes together
                db.commit()
                db.refresh(db_srf)
                
                return db_srf
                
            except IntegrityError as e:
                db.rollback()
                if "unique" in str(e.orig).lower() and "srf_no" in str(e.orig).lower():
                    if attempt < max_retries - 1:
                        continue  # Retry with new SRF number
                    else:
                        raise HTTPException(
                            status_code=400, 
                            detail="Unable to generate unique SRF number after multiple attempts"
                        )
                else:
                    raise HTTPException(status_code=400, detail=str(e.orig))
            
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to create SRF: {str(e)}")
        
        # This should never be reached due to the exception handling above
        raise HTTPException(status_code=400, detail="Maximum retries exceeded")
    
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
