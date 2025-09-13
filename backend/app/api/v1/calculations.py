# app/api/v1/calculations.py - Complete Calculation Engine API
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.calculation_engine_service import CalculationEngineService
from app.services.auto_deviation_service import AutoDeviationService
from app.api.v1.auth import get_current_user
from app.models.users import User
from app.models.jobs import Job
from app.models.calculations import JobCalculationResult

router = APIRouter()

# Pydantic Models for Request/Response
class CompleteCalculationRequest(BaseModel):
    measurement_data: Dict[str, Any]
    config_name: str = "hydraulic_torque_wrench_standard"
    auto_deviation_enabled: bool = True
    tolerance_overrides: Optional[Dict[str, float]] = None

class StageCalculationRequest(BaseModel):
    measurement_data: Dict[str, Any]
    stage_config: Optional[Dict[str, Any]] = None

class CalculationResponse(BaseModel):
    success: bool
    job_id: int
    stage_results: Dict[str, Any]
    final_results: Dict[str, Any]
    deviation_count: int
    calculation_status: str
    execution_time: Optional[str] = None

@router.post("/jobs/{job_id}/execute-complete-workflow", response_model=CalculationResponse)
async def execute_complete_calculation_workflow(
    job_id: int,
    request: CompleteCalculationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🎯 Execute complete 3-stage calculation workflow
    
    Stages:
    1. New RD Calculations (A-E components)
    2. UN_Resolution Calculations  
    3. Complete Uncertainty Budget (20 components)
    
    Features:
    - Auto-deviation detection
    - Email notifications
    - Complete audit trail
    - Excel formula compliance
    """
    try:
        # Verify job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Initialize calculation engine
        calc_engine = CalculationEngineService(db)
        
        # Record start time
        start_time = datetime.now()
        
        # Execute complete workflow
        workflow_result = calc_engine.execute_complete_calculation_workflow(
            job_id=job_id,
            measurement_data=request.measurement_data,
            config_name=request.config_name
        )
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        workflow_result["execution_time"] = f"{execution_time:.2f} seconds"
        
        # Handle deviations in background
        if workflow_result.get("deviation_reports"):
            background_tasks.add_task(
                handle_deviation_notifications,
                job_id,
                workflow_result["deviation_reports"],
                current_user.id
            )
        
        # Update job status
        job.calculation_status = "completed" if workflow_result["success"] else "failed"
        job.calculation_completed_at = datetime.now()
        db.commit()
        
        return CalculationResponse(
            success=workflow_result["success"],
            job_id=job_id,
            stage_results=workflow_result["stage_results"],
            final_results=workflow_result["final_results"],
            deviation_count=len(workflow_result.get("deviation_reports", [])),
            calculation_status="completed" if workflow_result["success"] else "failed",
            execution_time=workflow_result.get("execution_time")
        )
        
    except Exception as e:
        # Update job with error status
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.calculation_status = "failed"
            job.calculation_error = str(e)
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"Calculation workflow failed: {str(e)}")

@router.post("/jobs/{job_id}/calculate/stage1")
async def execute_stage1_calculations(
    job_id: int,
    request: StageCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🔍 Execute Stage 1: New RD Sheet Calculations
    
    Components:
    A. Repeatability (5 readings per point)
    B. Reproducibility (4 sequences)
    C. Output Drive (4 positions)
    D. Interface (4 positions)
    E. Loading Point (2 positions)
    """
    try:
        calc_engine = CalculationEngineService(db)
        
        # Get job configuration
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Execute Stage 1 only
        stage1_config = request.stage_config or calc_engine._get_engine_config("hydraulic_torque_wrench_standard")["stage1_methods"]
        
        stage1_result = calc_engine.execute_stage1_new_rd_calculations(
            job_id, request.measurement_data, stage1_config
        )
        
        return {
            "success": stage1_result["success"],
            "stage": 1,
            "stage_name": "New RD Sheet Calculations",
            "calculations": stage1_result["calculations"],
            "validation_results": stage1_result.get("validation_results", {}),
            "excel_compliance": stage1_result.get("excel_compliance", True)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stage 1 calculation failed: {str(e)}")

@router.post("/jobs/{job_id}/calculate/stage2")
async def execute_stage2_calculations(
    job_id: int,
    stage1_results: Dict[str, Any],
    request: StageCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📊 Execute Stage 2: UN_Resolution & Repeatability Calculations
    
    Components:
    - Target vs Reference analysis
    - Measurement error calculations
    - Corrected mean analysis
    - Type A uncertainty calculations
    """
    try:
        calc_engine = CalculationEngineService(db)
        
        # Get configuration
        stage2_config = request.stage_config or calc_engine._get_engine_config("hydraulic_torque_wrench_standard")["stage2_methods"]
        
        stage2_result = calc_engine.execute_stage2_un_resolution_calculations(
            job_id, stage1_results, stage2_config
        )
        
        return {
            "success": stage2_result["success"],
            "stage": 2,
            "stage_name": "UN_Resolution & Repeatability",
            "calculations": stage2_result["calculations"],
            "repeatability_analysis": stage2_result.get("repeatability_analysis", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stage 2 calculation failed: {str(e)}")

@router.post("/jobs/{job_id}/calculate/stage3")
async def execute_stage3_calculations(
    job_id: int,
    stage1_results: Dict[str, Any],
    stage2_results: Dict[str, Any],
    request: StageCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🎯 Execute Stage 3: Complete Uncertainty Budget
    
    Components:
    - All 20 uncertainty components
    - Combined uncertainty calculation
    - Expanded uncertainty with coverage factor
    - CMC calculations
    """
    try:
        calc_engine = CalculationEngineService(db)
        
        # Get configuration
        stage3_config = request.stage_config or calc_engine._get_engine_config("hydraulic_torque_wrench_standard")["stage3_methods"]
        
        stage3_result = calc_engine.execute_stage3_uncertainty_budget_calculations(
            job_id, stage1_results, stage2_results, stage3_config
        )
        
        return {
            "success": stage3_result["success"],
            "stage": 3,
            "stage_name": "Complete Uncertainty Budget",
            "uncertainty_budget": stage3_result["uncertainty_budget"],
            "summary": stage3_result.get("summary", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stage 3 calculation failed: {str(e)}")

@router.get("/jobs/{job_id}/calculation-results")
async def get_job_calculation_results(
    job_id: int,
    stage: Optional[int] = None,
    calculation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """📋 Get all calculation results for a job with optional filtering"""
    
    query = db.query(JobCalculationResult).filter(JobCalculationResult.job_id == job_id)
    
    if stage:
        query = query.filter(JobCalculationResult.calculation_stage == stage)
    
    if calculation_type:
        query = query.filter(JobCalculationResult.calculation_type == calculation_type)
    
    results = query.order_by(
        JobCalculationResult.calculation_stage,
        JobCalculationResult.calculation_order
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No calculation results found")
    
    # Organize results by stage
    organized_results = {
        "job_id": job_id,
        "total_calculations": len(results),
        "stages": {}
    }
    
    for result in results:
        stage_key = f"stage_{result.calculation_stage}"
        if stage_key not in organized_results["stages"]:
            organized_results["stages"][stage_key] = {}
        
        organized_results["stages"][stage_key][result.calculation_type] = {
            "calculated_values": result.calculated_values,
            "validation_status": result.validation_status,
            "exceeds_tolerance": result.exceeds_tolerance,
            "deviation_percentage": float(result.deviation_percentage) if result.deviation_percentage else None,
            "calculated_at": result.calculated_at,
            "calculated_by": result.calculated_by,
            "calculation_engine_version": result.calculation_engine_version
        }
    
    return organized_results

@router.get("/jobs/{job_id}/calculation-summary")
async def get_calculation_summary(
    job_id: int,
    db: Session = Depends(get_db)
):
    """📊 Get calculation summary with key metrics"""
    
    # Get job details
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Get all calculation results
    results = db.query(JobCalculationResult).filter(
        JobCalculationResult.job_id == job_id
    ).all()
    
    if not results:
        return {
            "job_id": job_id,
            "calculation_status": job.calculation_status,
            "message": "No calculations performed yet"
        }
    
    # Calculate summary metrics
    stages_completed = len(set(r.calculation_stage for r in results))
    total_calculations = len(results)
    failed_calculations = len([r for r in results if r.validation_status == "failed"])
    tolerance_violations = len([r for r in results if r.exceeds_tolerance])
    
    # Get latest calculation time
    latest_calculation = max(results, key=lambda r: r.calculated_at)
    
    return {
        "job_id": job_id,
        "calculation_status": job.calculation_status,
        "stages_completed": stages_completed,
        "total_calculations": total_calculations,
        "failed_calculations": failed_calculations,
        "tolerance_violations": tolerance_violations,
        "latest_calculation_at": latest_calculation.calculated_at,
        "calculation_engine_version": latest_calculation.calculation_engine_version,
        "overall_success_rate": ((total_calculations - failed_calculations) / total_calculations * 100) if total_calculations > 0 else 0
    }

@router.post("/jobs/{job_id}/recalculate")
async def recalculate_job(
    job_id: int,
    request: CompleteCalculationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔄 Recalculate job with new parameters or data"""
    
    # Clear existing calculation results
    db.query(JobCalculationResult).filter(JobCalculationResult.job_id == job_id).delete()
    db.commit()
    
    # Execute new calculation
    return await execute_complete_calculation_workflow(
        job_id, request, background_tasks, current_user, db
    )

@router.get("/calculation-engine/status")
async def get_calculation_engine_status(db: Session = Depends(get_db)):
    """🔧 Get calculation engine status and configuration"""
    
    from app.models.calculations import CalculationEngineConfig, FormulaLookupTable
    
    # Get active configurations
    configs = db.query(CalculationEngineConfig).filter(
        CalculationEngineConfig.is_active == True
    ).all()
    
    # Get lookup tables
    lookup_tables = db.query(FormulaLookupTable).filter(
        FormulaLookupTable.is_active == True
    ).all()
    
    return {
        "engine_status": "operational",
        "version": "2.0",
        "active_configurations": len(configs),
        "available_lookup_tables": len(lookup_tables),
        "supported_equipment_types": [
            "hydraulic_torque_wrench",
            "pressure_gauge",
            "torque_transducer"
        ],
        "calculation_stages": [
            {"stage": 1, "name": "New RD Calculations", "components": 5},
            {"stage": 2, "name": "UN_Resolution", "components": 10},
            {"stage": 3, "name": "Uncertainty Budget", "components": 20}
        ]
    }

# Background task functions
async def handle_deviation_notifications(job_id: int, deviation_reports: List[Dict], user_id: int):
    """Handle deviation notifications in background"""
    try:
        # This would integrate with your notification service
        # For now, just log the deviation
        print(f"🚨 Deviation detected for job {job_id}: {len(deviation_reports)} reports")
        
        # TODO: Implement email notification service
        # await send_deviation_email(job_id, deviation_reports, user_id)
        
    except Exception as e:
        print(f"❌ Failed to send deviation notification: {e}")