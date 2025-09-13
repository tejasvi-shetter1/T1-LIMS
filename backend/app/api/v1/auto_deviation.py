# app/api/v1/auto_deviation.py - Auto-Deviation System API
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel

from app.database import get_db
from app.services.auto_deviation_service import AutoDeviationService
from app.services.tolerance_service import ToleranceService
from app.services.email_service import EmailService
from app.api.v1.auth import get_current_user
from app.models.users import User
from app.models.deviations import DeviationReport
from app.models.jobs import Job

router = APIRouter()

# Pydantic Models
class ToleranceCheckResponse(BaseModel):
    job_id: int
    job_number: str
    nepl_work_id: str
    overall_status: str
    deviation_required: bool
    severity: str
    checks_performed: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    summary: Dict[str, Any]
    timestamp: str

class AutoDeviationResponse(BaseModel):
    job_id: int
    generated_deviations: List[Dict[str, Any]]
    notifications_sent: List[Dict[str, Any]]
    next_actions: List[str]
    summary: Dict[str, Any]

class CustomerResponseUpdate(BaseModel):
    client_decision: str  # "ACCEPT", "REJECT", "CONDITIONAL"
    client_comments: Optional[str] = None
    client_decision_date: Optional[date] = None

class DeviationStatusResponse(BaseModel):
    job_id: int
    job_number: str
    overall_deviation_status: str
    certificate_generation_allowed: bool
    deviations: List[Dict[str, Any]]
    total_deviations: int
    approved_deviations: int
    rejected_deviations: int
    pending_deviations: int

@router.post("/jobs/{job_id}/check-tolerances", response_model=ToleranceCheckResponse)
async def check_job_tolerances(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🎯 Run complete tolerance checking for a job
    
    Performs comprehensive tolerance checks including:
    - Environmental conditions
    - Calculation results
    - Uncertainty limits
    - Measurement errors
    - Standards validity
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Run tolerance checks
        tolerance_results = ToleranceService.check_job_tolerances(db, job_id)
        tolerance_results["timestamp"] = datetime.now().isoformat()
        
        return ToleranceCheckResponse(**tolerance_results)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tolerance check failed: {str(e)}")

@router.post("/jobs/{job_id}/auto-generate-deviations", response_model=AutoDeviationResponse)
async def auto_generate_deviations(
    job_id: int,
    background_tasks: BackgroundTasks,
    send_notifications: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🚨 Auto-generate deviation reports and send notifications
    
    This endpoint:
    1. Runs tolerance checks
    2. Creates deviation reports for failures
    3. Sends email notifications to customers
    4. Updates job status
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Generate deviations
        generated_deviations = AutoDeviationService.auto_generate_deviation_reports(
            db, job_id, current_user.username
        )
        
        # Get customer details for notifications
        customer = job.inward.srf_item.srf.customer
        notifications_sent = []
        
        # Send email notifications if requested
        if send_notifications and generated_deviations:
            for deviation in generated_deviations:
                try:
                    # Send customer notification in background
                    background_tasks.add_task(
                        EmailService.send_deviation_notification,
                        deviation,
                        job,
                        customer.email or customer.notification_email,
                        customer.name
                    )
                    
                    notifications_sent.append({
                        "deviation_number": deviation.deviation_number,
                        "customer_email": customer.email or customer.notification_email,
                        "notification_type": "deviation_alert",
                        "status": "queued"
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to queue notification for deviation {deviation.id}: {e}")
        
        # Update job status
        if generated_deviations:
            job.deviation_required = True
            job.deviation_resolved = False
            job.can_generate_certificate = False
            job.status = "deviation_pending"
            db.commit()
        
        # Prepare response
        deviation_list = [
            {
                "id": dev.id,
                "deviation_number": dev.deviation_number,
                "deviation_type": dev.deviation_type,
                "severity": dev.severity,
                "status": dev.status,
                "customer_approval_required": True,
                "created_at": dev.created_at.isoformat(),
                "technical_impact": dev.technical_impact,
                "customer_impact": dev.customer_impact
            }
            for dev in generated_deviations
        ]
        
        next_actions = []
        if generated_deviations:
            next_actions = [
                "Customer notifications sent via email",
                "Awaiting customer approval decisions",
                "Certificate generation on hold until approval",
                "Monitor deviation status in dashboard",
                f"Contact customer if no response within 48 hours"
            ]
        else:
            next_actions = [
                "No deviations detected",
                "Job passed all tolerance checks",
                "Ready for certificate generation"
            ]
        
        summary = {
            "total_deviations": len(generated_deviations),
            "high_severity": len([d for d in generated_deviations if d.severity == "high"]),
            "medium_severity": len([d for d in generated_deviations if d.severity == "medium"]),
            "low_severity": len([d for d in generated_deviations if d.severity == "low"]),
            "notifications_sent": len(notifications_sent),
            "job_status": job.status
        }
        
        return AutoDeviationResponse(
            job_id=job_id,
            generated_deviations=deviation_list,
            notifications_sent=notifications_sent,
            next_actions=next_actions,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-deviation generation failed: {str(e)}")

@router.put("/deviations/{deviation_id}/customer-approve")
async def customer_approve_deviation(
    deviation_id: int,
    approval_data: CustomerResponseUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    ✅ Customer approval endpoint for deviations
    
    Allows customers to approve, reject, or conditionally accept deviations.
    Triggers appropriate workflows based on customer decision.
    """
    try:
        # Get deviation
        deviation = db.query(DeviationReport).filter(DeviationReport.id == deviation_id).first()
        if not deviation:
            raise HTTPException(status_code=404, detail=f"Deviation {deviation_id} not found")
        
        # Update deviation with customer response
        deviation.client_decision = approval_data.client_decision
        deviation.client_comments = approval_data.client_comments
        deviation.client_decision_date = approval_data.client_decision_date or date.today()
        deviation.client_notified_at = datetime.now()
        
        # Update status based on decision
        if approval_data.client_decision == "ACCEPT":
            deviation.status = "approved"
        elif approval_data.client_decision == "REJECT":
            deviation.status = "rejected"
        elif approval_data.client_decision == "CONDITIONAL":
            deviation.status = "conditional_approval"
        
        # Get job and update status
        job = deviation.job
        
        if approval_data.client_decision == "ACCEPT":
            # Check if all deviations for this job are resolved
            pending_deviations = db.query(DeviationReport).filter(
                DeviationReport.job_id == job.id,
                DeviationReport.status.in_(["open", "investigating", "pending_approval"])
            ).count()
            
            if pending_deviations == 0:
                job.deviation_resolved = True
                job.can_generate_certificate = True
                job.status = "approved"
            
            # Send notification to lab team
            lab_team_emails = EmailService.get_lab_team_emails()
            background_tasks.add_task(
                EmailService.send_deviation_approved_notification,
                deviation,
                job,
                lab_team_emails
            )
            
            response_message = "Deviation approved successfully"
            next_steps = [
                "Certificate generation authorized",
                "Lab team notified of approval",
                "Deviation details will be included in certificate"
            ]
            
        elif approval_data.client_decision == "REJECT":
            job.deviation_resolved = False
            job.can_generate_certificate = False
            job.status = "deviation_rejected"
            
            # Send notification to lab team
            lab_team_emails = EmailService.get_lab_team_emails()
            background_tasks.add_task(
                EmailService.send_deviation_rejected_notification,
                deviation,
                job,
                lab_team_emails
            )
            
            response_message = "Deviation rejected - corrective action required"
            next_steps = [
                "Lab team notified of rejection",
                "Review customer comments and feedback",
                "Implement corrective actions",
                "Consider re-calibration if necessary",
                "Contact customer to discuss next steps"
            ]
            
        else:  # CONDITIONAL
            job.deviation_resolved = True
            job.can_generate_certificate = True
            job.status = "conditional_approval"
            
            response_message = "Deviation conditionally approved"
            next_steps = [
                "Certificate generation authorized with conditions",
                "Include customer conditions in certificate",
                "Document conditional acceptance"
            ]
        
        db.commit()
        
        return {
            "success": True,
            "message": response_message,
            "deviation_id": deviation.id,
            "deviation_number": deviation.deviation_number,
            "customer_decision": approval_data.client_decision,
            "job_status": job.status,
            "certificate_generation_ready": job.can_generate_certificate,
            "next_steps": next_steps
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Customer approval failed: {str(e)}")

@router.get("/jobs/{job_id}/deviation-status", response_model=DeviationStatusResponse)
async def get_job_deviation_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    📊 Get comprehensive deviation status for a job
    """
    try:
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Get all deviations for the job
        deviations = db.query(DeviationReport).filter(DeviationReport.job_id == job_id).all()
        
        deviation_summary = []
        for dev in deviations:
            deviation_summary.append({
                "id": dev.id,
                "deviation_number": dev.deviation_number,
                "deviation_type": dev.deviation_type,
                "status": dev.status,
                "severity": dev.severity,
                "customer_decision": dev.client_decision,
                "customer_comments": dev.client_comments,
                "created_at": dev.created_at.isoformat(),
                "client_decision_date": dev.client_decision_date.isoformat() if dev.client_decision_date else None,
                "technical_impact": dev.technical_impact,
                "customer_impact": dev.customer_impact
            })
        
        # Calculate statistics
        approved_deviations = len([d for d in deviations if d.client_decision == "ACCEPT"])
        rejected_deviations = len([d for d in deviations if d.client_decision == "REJECT"])
        pending_deviations = len([d for d in deviations if not d.client_decision])
        
        # Determine overall status
        if not deviations:
            overall_status = "no_deviations"
        elif pending_deviations > 0:
            overall_status = "pending_approval"
        elif rejected_deviations > 0:
            overall_status = "rejected"
        else:
            overall_status = "resolved"
        
        return DeviationStatusResponse(
            job_id=job_id,
            job_number=job.job_number,
            overall_deviation_status=overall_status,
            certificate_generation_allowed=job.can_generate_certificate,
            deviations=deviation_summary,
            total_deviations=len(deviations),
            approved_deviations=approved_deviations,
            rejected_deviations=rejected_deviations,
            pending_deviations=pending_deviations
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get deviation status: {str(e)}")

@router.get("/dashboard/summary")
async def get_deviation_dashboard_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    📊 Get deviation dashboard summary with analytics
    """
    try:
        query = db.query(DeviationReport)
        
        if date_from:
            query = query.filter(DeviationReport.created_at >= date_from)
        
        if date_to:
            query = query.filter(DeviationReport.created_at <= date_to)
        
        deviations = query.all()
        
        # Calculate metrics
        total_deviations = len(deviations)
        open_deviations = len([d for d in deviations if d.status in ["open", "investigating"]])
        resolved_deviations = len([d for d in deviations if d.status in ["approved", "resolved"]])
        rejected_deviations = len([d for d in deviations if d.status == "rejected"])
        
        # Group by severity
        severity_breakdown = {
            "high": len([d for d in deviations if d.severity == "high"]),
            "medium": len([d for d in deviations if d.severity == "medium"]),
            "low": len([d for d in deviations if d.severity == "low"])
        }
        
        # Group by type
        type_breakdown = {}
        for deviation in deviations:
            dev_type = deviation.deviation_type or "unknown"
            type_breakdown[dev_type] = type_breakdown.get(dev_type, 0) + 1
        
        # Customer response analysis
        customer_responses = {
            "approved": len([d for d in deviations if d.client_decision == "ACCEPT"]),
            "rejected": len([d for d in deviations if d.client_decision == "REJECT"]),
            "conditional": len([d for d in deviations if d.client_decision == "CONDITIONAL"]),
            "pending": len([d for d in deviations if not d.client_decision])
        }
        
        return {
            "summary": {
                "total_deviations": total_deviations,
                "open_deviations": open_deviations,
                "resolved_deviations": resolved_deviations,
                "rejected_deviations": rejected_deviations,
                "resolution_rate": (resolved_deviations / total_deviations * 100) if total_deviations > 0 else 0,
                "approval_rate": (customer_responses["approved"] / total_deviations * 100) if total_deviations > 0 else 0
            },
            "severity_breakdown": severity_breakdown,
            "type_breakdown": type_breakdown,
            "customer_responses": customer_responses,
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "trends": {
                "most_common_deviation_type": max(type_breakdown.items(), key=lambda x: x[1])[0] if type_breakdown else None,
                "average_resolution_time": "2.5 days",  # TODO: Calculate from actual data
                "customer_satisfaction": "85%"  # TODO: Calculate from approval rates
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get dashboard summary: {str(e)}")

@router.post("/test-email-notification")
async def test_email_notification(
    deviation_id: int,
    test_email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🧪 Test email notification system (for development/testing)
    """
    try:
        deviation = db.query(DeviationReport).filter(DeviationReport.id == deviation_id).first()
        if not deviation:
            raise HTTPException(status_code=404, detail="Deviation not found")
        
        job = deviation.job
        
        result = EmailService.send_deviation_notification(
            deviation=deviation,
            job=job,
            customer_email=test_email,
            customer_name="Test Customer"
        )
        
        return {
            "success": result["success"],
            "message": f"Test email sent to {test_email}",
            "deviation_number": deviation.deviation_number,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Test email failed: {str(e)}")