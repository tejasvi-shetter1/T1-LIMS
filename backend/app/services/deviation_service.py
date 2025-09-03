from sqlalchemy.orm import Session
from app.models.deviations import DeviationReport, DeviationAction
from app.schemas.deviations import DeviationCreate, CustomerResponseUpdate
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class DeviationService:
    
    @staticmethod
    def create_deviation(db: Session, deviation_data: DeviationCreate) -> DeviationReport:
        """Create new deviation with automatic number generation"""
        
        # Auto-generate deviation number
        deviation_number = DeviationService._generate_deviation_number(db)
        
        deviation = DeviationReport(
            job_id=deviation_data.job_id,
            deviation_number=deviation_number,
            deviation_type=deviation_data.deviation_type,
            severity=deviation_data.severity,
            description=deviation_data.description,
            technical_impact=deviation_data.technical_impact,
            customer_impact=deviation_data.customer_impact,
            status="OPEN",
            identified_by=deviation_data.identified_by,
            created_by=deviation_data.identified_by
        )
        
        db.add(deviation)
        db.flush()
        
        # Log action
        DeviationService._log_action(
            db, deviation.id, "CREATED", deviation_data.identified_by,
            f"Deviation created: {deviation_data.deviation_type}",
            None, "OPEN"
        )
        
        db.commit()
        db.refresh(deviation)
        
        logger.info(f"Deviation {deviation_number} created")
        return deviation
    
    @staticmethod
    def update_customer_response(
        db: Session, 
        deviation_id: int, 
        response_data: CustomerResponseUpdate, 
        customer_user: str
    ) -> DeviationReport:
        """Handle customer accept/reject response"""
        
        deviation = db.query(DeviationReport).filter(DeviationReport.id == deviation_id).first()
        if not deviation:
            raise ValueError("Deviation not found")
        
        old_status = deviation.status
        
        # Update deviation
        deviation.client_decision = response_data.client_decision
        deviation.client_comments = response_data.client_comments
        deviation.client_decision_date = datetime.utcnow()
        deviation.updated_by = customer_user
        
        # Update status based on decision
        if response_data.client_decision == "ACCEPT":
            deviation.status = "CUSTOMER_ACCEPTED"
        else:
            deviation.status = "CUSTOMER_REJECTED"
        
        # Log action
        DeviationService._log_action(
            db, deviation.id, "CUSTOMER_RESPONSE", customer_user,
            f"Customer {response_data.client_decision}: {response_data.client_comments or ''}",
            old_status, deviation.status
        )
        
        db.commit()
        db.refresh(deviation)
        
        logger.info(f"Customer response for deviation {deviation.deviation_number}: {response_data.client_decision}")
        return deviation
    
    @staticmethod
    def resolve_deviation(
        db: Session, 
        deviation_id: int, 
        resolution_actions: str, 
        resolved_by: str
    ) -> DeviationReport:
        """Resolve deviation"""
        
        deviation = db.query(DeviationReport).filter(DeviationReport.id == deviation_id).first()
        if not deviation:
            raise ValueError("Deviation not found")
        
        old_status = deviation.status
        
        # Update deviation
        deviation.status = "RESOLVED"
        deviation.resolved_by = resolved_by
        deviation.resolved_at = datetime.utcnow()
        deviation.resolution_actions = resolution_actions
        deviation.updated_by = resolved_by
        
        # Update job certificate generation status
        DeviationService._update_job_certificate_status(db, deviation.job_id)
        
        # Log action
        DeviationService._log_action(
            db, deviation.id, "RESOLVED", resolved_by,
            f"Deviation resolved: {resolution_actions}",
            old_status, "RESOLVED"
        )
        
        db.commit()
        db.refresh(deviation)
        
        logger.info(f"Deviation {deviation.deviation_number} resolved")
        return deviation
    
    @staticmethod
    def _generate_deviation_number(db: Session) -> str:
        """Generate next deviation number"""
        current_year = datetime.now().year
        
        last_deviation = db.query(DeviationReport)\
            .filter(DeviationReport.deviation_number.like(f"DEV-{current_year}-%"))\
            .order_by(DeviationReport.id.desc())\
            .first()
        
        if last_deviation:
            try:
                last_seq = int(last_deviation.deviation_number.split('-')[-1])
                next_seq = last_seq + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1
        
        return f"DEV-{current_year}-{next_seq:03d}"
    
    @staticmethod
    def _log_action(
        db: Session, 
        deviation_id: int, 
        action_type: str, 
        action_by: str, 
        comments: str,
        old_status: Optional[str],
        new_status: str
    ):
        """Log deviation action for audit trail"""
        
        action = DeviationAction(
            deviation_id=deviation_id,
            action_type=action_type,
            action_by=action_by,
            action_at=datetime.utcnow(),
            comments=comments,
            old_status=old_status,
            new_status=new_status
        )
        db.add(action)
    
    @staticmethod
    def _update_job_certificate_status(db: Session, job_id: int):
        """Update job certificate generation status after deviation resolution"""
        from app.models.jobs import Job
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        # Check if all deviations for this job are resolved
        unresolved_deviations = db.query(DeviationReport).filter(
            DeviationReport.job_id == job_id,
            DeviationReport.status.not_in(["RESOLVED", "CLOSED"])
        ).count()
        
        if unresolved_deviations == 0:
            job.deviation_resolved = True
            job.can_generate_certificate = True
        else:
            job.deviation_resolved = False
            job.can_generate_certificate = False
