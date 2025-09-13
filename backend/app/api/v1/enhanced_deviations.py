# app/api/v1/enhanced_deviations.py - Enhanced Deviation Management API
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, date

from app.database import get_db
from app.services.auto_deviation_service import AutoDeviationService
from app.api.v1.auth import get_current_user
from app.models.users import User
from app.models.deviations import DeviationReport, DeviationAction
from app.models.jobs import Job

router = APIRouter()

# Pydantic Models
class AutoDeviationRequest(BaseModel):
    job_id: int
    calculation_results: Dict[str, Any]
    tolerance_overrides: Optional[Dict[str, float]] = None

class DeviationAnalysisResponse(BaseModel):
    job_id: int
    total_deviations: int
    high_severity: int
    medium_severity: int
    low_severity: int
    auto_generated: int
    manual_created: int
    resolved: int
    pending: int

class DeviationActionRequest(BaseModel):
    action_type: str  # "acknowledge", "investigate", "resolve", "escalate"
    comments: str
    resolution_actions: Optional[str] = None

@router.post("/auto-detect")
async def auto_detect_deviations(
    request: AutoDeviationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🚨 Auto-detect deviations from calculation results
    
    Analyzes calculation results against tolerance limits and creates
    deviation reports automatically when thresholds are exceeded.
    """
    try:
        deviation_service = AutoDeviationService(db)
        
        # Analyze calculation results for deviations
        detected_deviations = deviation_service.analyze_calculation_results(
            job_id=request.job_id,
            calculation_results=request.calculation_results,
            tolerance_overrides=request.tolerance_overrides
        )
        
        created_deviations = []
        
        for deviation_data in detected_deviations:
            # Create deviation report
            deviation = deviation_service.create_auto_deviation_report(
                job_id=request.job_id,
                deviation_data=deviation_data,
                identified_by=current_user.username
            )
            
            created_deviations.append({
                "deviation_id": deviation.id,
                "deviation_number": deviation.deviation_number,
                "severity": deviation.severity,
                "description": deviation.description
            })
            
            # Send notifications in background
            background_tasks.add_task(
                send_deviation_notification,
                deviation.id,
                current_user.id
            )
        
        return {
            "success": True,
            "job_id": request.job_id,
            "deviations_detected": len(created_deviations),
            "created_deviations": created_deviations,
            "analysis_summary": {
                "total_violations": len(detected_deviations),
                "high_severity": len([d for d in detected_deviations if d.get("severity") == "high"]),
                "medium_severity": len([d for d in detected_deviations if d.get("severity") == "medium"]),
                "low_severity": len([d for d in detected_deviations if d.get("severity") == "low"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-deviation detection failed: {str(e)}")

@router.get("/jobs/{job_id}/analysis", response_model=DeviationAnalysisResponse)
async def get_job_deviation_analysis(
    job_id: int,
    db: Session = Depends(get_db)
):
    """📊 Get comprehensive deviation analysis for a job"""
    
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Get all deviations for the job
    deviations = db.query(DeviationReport).filter(DeviationReport.job_id == job_id).all()
    
    # Analyze deviations
    total_deviations = len(deviations)
    high_severity = len([d for d in deviations if d.severity == "high"])
    medium_severity = len([d for d in deviations if d.severity == "medium"])
    low_severity = len([d for d in deviations if d.severity == "low"])
    
    auto_generated = len([d for d in deviations if d.identified_by == "AUTO_CALCULATION_ENGINE"])
    manual_created = total_deviations - auto_generated
    
    resolved = len([d for d in deviations if d.status == "resolved"])
    pending = len([d for d in deviations if d.status in ["open", "investigating", "pending_approval"]])
    
    return DeviationAnalysisResponse(
        job_id=job_id,
        total_deviations=total_deviations,
        high_severity=high_severity,
        medium_severity=medium_severity,
        low_severity=low_severity,
        auto_generated=auto_generated,
        manual_created=manual_created,
        resolved=resolved,
        pending=pending
    )

@router.post("/deviations/{deviation_id}/actions")
async def create_deviation_action(
    deviation_id: int,
    request: DeviationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔧 Create action on deviation report"""
    
    # Verify deviation exists
    deviation = db.query(DeviationReport).filter(DeviationReport.id == deviation_id).first()
    if not deviation:
        raise HTTPException(status_code=404, detail=f"Deviation {deviation_id} not found")
    
    # Create deviation action
    action = DeviationAction(
        deviation_id=deviation_id,
        action_type=request.action_type,
        action_by=current_user.username,
        action_at=datetime.now(),
        comments=request.comments,
        old_status=deviation.status
    )
    
    # Update deviation status based on action
    if request.action_type == "acknowledge":
        deviation.status = "acknowledged"
    elif request.action_type == "investigate":
        deviation.status = "investigating"
    elif request.action_type == "resolve":
        deviation.status = "resolved"
        deviation.resolved_at = datetime.now()
        deviation.resolved_by = current_user.username
        if request.resolution_actions:
            deviation.resolution_actions = request.resolution_actions
    elif request.action_type == "escalate":
        deviation.status = "escalated"
    
    action.new_status = deviation.status
    
    db.add(action)
    db.commit()
    
    return {
        "success": True,
        "action_id": action.id,
        "deviation_id": deviation_id,
        "old_status": action.old_status,
        "new_status": action.new_status,
        "action_type": request.action_type,
        "created_at": action.action_at
    }

@router.get("/deviations/{deviation_id}/actions")
async def get_deviation_actions(
    deviation_id: int,
    db: Session = Depends(get_db)
):
    """📋 Get all actions for a deviation"""
    
    actions = db.query(DeviationAction).filter(
        DeviationAction.deviation_id == deviation_id
    ).order_by(DeviationAction.action_at.desc()).all()
    
    return {
        "deviation_id": deviation_id,
        "total_actions": len(actions),
        "actions": [
            {
                "id": action.id,
                "action_type": action.action_type,
                "action_by": action.action_by,
                "action_at": action.action_at,
                "comments": action.comments,
                "old_status": action.old_status,
                "new_status": action.new_status
            }
            for action in actions
        ]
    }

@router.get("/tolerance-limits")
async def get_tolerance_limits(
    equipment_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """📏 Get tolerance limits for deviation detection"""
    
    from app.models.calculations import CalculationEngineConfig
    
    query = db.query(CalculationEngineConfig).filter(CalculationEngineConfig.is_active == True)
    
    if equipment_type:
        query = query.filter(CalculationEngineConfig.equipment_type == equipment_type)
    
    configs = query.all()
    
    tolerance_limits = {}
    for config in configs:
        if config.tolerance_config:
            tolerance_limits[config.config_name] = config.tolerance_config
    
    return {
        "available_limits": tolerance_limits,
        "default_limits": {
            "repeatability_max_deviation": 4.0,
            "uncertainty_max_percent": 3.0,
            "reproducibility_max_error": 1.0,
            "output_drive_max_error": 1.0,
            "interface_max_error": 1.0,
            "loading_point_max_error": 2.0
        }
    }

@router.post("/tolerance-limits/update")
async def update_tolerance_limits(
    config_name: str,
    tolerance_limits: Dict[str, float],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔧 Update tolerance limits for deviation detection"""
    
    from app.models.calculations import CalculationEngineConfig
    
    config = db.query(CalculationEngineConfig).filter(
        CalculationEngineConfig.config_name == config_name
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuration {config_name} not found")
    
    # Update tolerance config
    config.tolerance_config = tolerance_limits
    config.updated_at = datetime.now()
    
    db.commit()
    
    return {
        "success": True,
        "config_name": config_name,
        "updated_limits": tolerance_limits,
        "updated_by": current_user.username,
        "updated_at": config.updated_at
    }

@router.get("/dashboard/summary")
async def get_deviation_dashboard_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """📊 Get deviation dashboard summary"""
    
    query = db.query(DeviationReport)
    
    if date_from:
        query = query.filter(DeviationReport.created_at >= date_from)
    
    if date_to:
        query = query.filter(DeviationReport.created_at <= date_to)
    
    deviations = query.all()
    
    # Calculate metrics
    total_deviations = len(deviations)
    open_deviations = len([d for d in deviations if d.status in ["open", "investigating"]])
    resolved_deviations = len([d for d in deviations if d.status == "resolved"])
    
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
    
    return {
        "summary": {
            "total_deviations": total_deviations,
            "open_deviations": open_deviations,
            "resolved_deviations": resolved_deviations,
            "resolution_rate": (resolved_deviations / total_deviations * 100) if total_deviations > 0 else 0
        },
        "severity_breakdown": severity_breakdown,
        "type_breakdown": type_breakdown,
        "period": {
            "from": date_from,
            "to": date_to
        }
    }

# Background task functions
async def send_deviation_notification(deviation_id: int, user_id: int):
    """Send deviation notification in background"""
    try:
        # TODO: Implement email notification service
        print(f"📧 Sending deviation notification for deviation {deviation_id}")
        
    except Exception as e:
        print(f"❌ Failed to send deviation notification: {e}")