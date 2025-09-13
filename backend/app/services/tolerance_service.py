# app/services/tolerance_service.py - Tolerance Checking Engine
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Any
from decimal import Decimal
from app.models.measurements import UncertaintyCalculation
from app.models.jobs import Job
from app.models.calculations import JobCalculationResult
import logging

logger = logging.getLogger(__name__)

class ToleranceService:
    """
    Tolerance Checking Engine for Auto-Deviation Detection
    
    Implements tolerance limits based on Excel analysis and ISO standards
    """
    
    # Tolerance limits from Excel analysis and ISO 6789 standards
    TOLERANCE_LIMITS = {
        # Primary tolerance limits
        "expanded_uncertainty_percent": 5.0,      # Max 5% expanded uncertainty (ISO limit)
        "repeatability_deviation_percent": 4.0,   # Max ±4% repeatability deviation
        "reproducibility_error_nm": 1.5,          # Max 1.5 Nm reproducibility error
        "output_drive_error_nm": 1.0,             # Max 1.0 Nm output drive error
        "interface_error_nm": 1.0,                # Max 1.0 Nm interface error
        "loading_point_error_nm": 2.0,            # Max 2.0 Nm loading point error
        
        # Environmental conditions (from Excel)
        "environmental_temp_min": 20.0,           # Min 20°C temperature
        "environmental_temp_max": 30.0,           # Max 30°C temperature
        "environmental_humidity_min": 45.0,       # Min 45% humidity
        "environmental_humidity_max": 75.0,       # Max 75% humidity
        
        # Measurement quality limits
        "measurement_error_limit": 20.0,          # Max 20% measurement error
        "combined_uncertainty_limit": 3.0,        # Max 3% combined uncertainty
        "coverage_factor": 2.0,                   # Standard coverage factor k=2
        
        # CMC and calibration limits
        "cmc_compliance_limit": 0.6,              # Max 0.6% CMC limit
        "calibration_validity_days": 365,         # Standard validity period
        
        # Stage-specific limits
        "stage1_max_deviations": 2,               # Max 2 deviations in Stage 1
        "stage2_resolution_limit": 0.1,           # Min resolution requirement
        "stage3_uncertainty_components": 20       # Required uncertainty components
    }
    
    @staticmethod
    def check_job_tolerances(db: Session, job_id: int) -> Dict[str, Any]:
        """
        🎯 Complete tolerance checking for a job
        Returns comprehensive tolerance check results
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        tolerance_results = {
            "job_id": job_id,
            "job_number": job.job_number,
            "nepl_work_id": job.nepl_work_id,
            "overall_status": "PASS",
            "checks_performed": [],
            "failures": [],
            "warnings": [],
            "deviation_required": False,
            "severity": "LOW",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be updated
        }
        
        try:
            # Check 1: Environmental conditions
            env_check = ToleranceService._check_environmental_conditions(job)
            tolerance_results["checks_performed"].append(env_check)
            if not env_check["passed"]:
                tolerance_results["failures"].append(env_check)
                tolerance_results["overall_status"] = "FAIL"
                tolerance_results["deviation_required"] = True
                if env_check["severity"] == "HIGH":
                    tolerance_results["severity"] = "HIGH"
            
            # Check 2: Calculation results tolerance
            calc_check = ToleranceService._check_calculation_tolerances(db, job_id)
            tolerance_results["checks_performed"].append(calc_check)
            if not calc_check["passed"]:
                tolerance_results["failures"].append(calc_check)
                tolerance_results["overall_status"] = "FAIL"
                tolerance_results["deviation_required"] = True
                if calc_check["severity"] == "HIGH":
                    tolerance_results["severity"] = "HIGH"
            
            # Check 3: Uncertainty calculations
            uncertainty_check = ToleranceService._check_uncertainty_limits(db, job_id)
            tolerance_results["checks_performed"].append(uncertainty_check)
            if not uncertainty_check["passed"]:
                tolerance_results["failures"].append(uncertainty_check)
                tolerance_results["overall_status"] = "FAIL"
                tolerance_results["deviation_required"] = True
                if uncertainty_check["severity"] == "HIGH":
                    tolerance_results["severity"] = "HIGH"
            
            # Check 4: Measurement errors
            measurement_check = ToleranceService._check_measurement_errors(db, job_id)
            tolerance_results["checks_performed"].append(measurement_check)
            if not measurement_check["passed"]:
                if measurement_check["severity"] == "HIGH":
                    tolerance_results["failures"].append(measurement_check)
                    tolerance_results["overall_status"] = "FAIL"
                    tolerance_results["deviation_required"] = True
                    tolerance_results["severity"] = "HIGH"
                else:
                    tolerance_results["warnings"].append(measurement_check)
            
            # Check 5: Standards validity
            standards_check = ToleranceService._check_standards_validity(db, job_id)
            tolerance_results["checks_performed"].append(standards_check)
            if not standards_check["passed"]:
                tolerance_results["failures"].append(standards_check)
                tolerance_results["overall_status"] = "FAIL"
                tolerance_results["deviation_required"] = True
                tolerance_results["severity"] = "HIGH"
            
            # Final assessment
            tolerance_results["summary"] = {
                "total_checks": len(tolerance_results["checks_performed"]),
                "passed_checks": len([c for c in tolerance_results["checks_performed"] if c["passed"]]),
                "failed_checks": len(tolerance_results["failures"]),
                "warning_checks": len(tolerance_results["warnings"]),
                "pass_rate": len([c for c in tolerance_results["checks_performed"] if c["passed"]]) / len(tolerance_results["checks_performed"]) * 100
            }
            
            logger.info(f"Tolerance check completed for job {job_id}: {tolerance_results['overall_status']}")
            
        except Exception as e:
            logger.error(f"Tolerance checking failed for job {job_id}: {e}")
            tolerance_results["overall_status"] = "ERROR"
            tolerance_results["error"] = str(e)
        
        return tolerance_results
    
    @staticmethod
    def _check_environmental_conditions(job: Job) -> Dict[str, Any]:
        """Check environmental conditions against limits"""
        check_result = {
            "check_type": "environmental_conditions",
            "check_name": "Environmental Conditions Validation",
            "passed": True,
            "severity": "MEDIUM",
            "details": [],
            "measurements": {},
            "recommendation": "Environmental conditions acceptable"
        }
        
        # Temperature checks
        if job.temp_before:
            temp_before = float(job.temp_before)
            check_result["measurements"]["temp_before"] = temp_before
            
            if temp_before < ToleranceService.TOLERANCE_LIMITS["environmental_temp_min"]:
                check_result["passed"] = False
                check_result["severity"] = "HIGH"
                check_result["details"].append(
                    f"Temperature before ({temp_before}°C) below minimum limit "
                    f"({ToleranceService.TOLERANCE_LIMITS['environmental_temp_min']}°C)"
                )
                check_result["recommendation"] = "Repeat calibration under proper environmental conditions"
            
            elif temp_before > ToleranceService.TOLERANCE_LIMITS["environmental_temp_max"]:
                check_result["passed"] = False
                check_result["severity"] = "HIGH"
                check_result["details"].append(
                    f"Temperature before ({temp_before}°C) above maximum limit "
                    f"({ToleranceService.TOLERANCE_LIMITS['environmental_temp_max']}°C)"
                )
                check_result["recommendation"] = "Repeat calibration under proper environmental conditions"
        
        if job.temp_after:
            temp_after = float(job.temp_after)
            check_result["measurements"]["temp_after"] = temp_after
            
            if temp_after < ToleranceService.TOLERANCE_LIMITS["environmental_temp_min"] or \
               temp_after > ToleranceService.TOLERANCE_LIMITS["environmental_temp_max"]:
                check_result["passed"] = False
                check_result["severity"] = "HIGH"
                check_result["details"].append(f"Temperature after ({temp_after}°C) outside limits")
        
        # Humidity checks
        if job.humidity_before:
            humidity_before = float(job.humidity_before) * 100  # Convert to percentage
            check_result["measurements"]["humidity_before"] = humidity_before
            
            if humidity_before < ToleranceService.TOLERANCE_LIMITS["environmental_humidity_min"] or \
               humidity_before > ToleranceService.TOLERANCE_LIMITS["environmental_humidity_max"]:
                check_result["passed"] = False
                check_result["details"].append(f"Humidity before ({humidity_before}%) outside limits")
        
        if job.humidity_after:
            humidity_after = float(job.humidity_after) * 100
            check_result["measurements"]["humidity_after"] = humidity_after
            
            if humidity_after < ToleranceService.TOLERANCE_LIMITS["environmental_humidity_min"] or \
               humidity_after > ToleranceService.TOLERANCE_LIMITS["environmental_humidity_max"]:
                check_result["passed"] = False
                check_result["details"].append(f"Humidity after ({humidity_after}%) outside limits")
        
        return check_result
    
    @staticmethod
    def _check_calculation_tolerances(db: Session, job_id: int) -> Dict[str, Any]:
        """Check calculation results against tolerance limits"""
        check_result = {
            "check_type": "calculation_tolerances",
            "check_name": "Calculation Results Validation",
            "passed": True,
            "severity": "MEDIUM",
            "details": [],
            "measurements": {},
            "recommendation": "Calculation results within acceptable limits"
        }
        
        # Get calculation results
        calc_results = db.query(JobCalculationResult).filter(
            JobCalculationResult.job_id == job_id
        ).all()
        
        for result in calc_results:
            if result.calculated_values:
                # Check repeatability deviations
                if result.calculation_type == "repeatability":
                    max_deviation = result.calculated_values.get("max_deviation_percent", 0)
                    check_result["measurements"]["repeatability_deviation"] = max_deviation
                    
                    if abs(max_deviation) > ToleranceService.TOLERANCE_LIMITS["repeatability_deviation_percent"]:
                        check_result["passed"] = False
                        check_result["severity"] = "HIGH"
                        check_result["details"].append(
                            f"Repeatability deviation ({max_deviation:.3f}%) exceeds ±{ToleranceService.TOLERANCE_LIMITS['repeatability_deviation_percent']}% limit"
                        )
                        check_result["recommendation"] = "Review measurement procedure and equipment stability"
                
                # Check reproducibility errors
                elif result.calculation_type == "reproducibility":
                    error_nm = result.calculated_values.get("reproducibility_error_nm", 0)
                    check_result["measurements"]["reproducibility_error"] = error_nm
                    
                    if error_nm > ToleranceService.TOLERANCE_LIMITS["reproducibility_error_nm"]:
                        check_result["passed"] = False
                        check_result["severity"] = "HIGH"
                        check_result["details"].append(
                            f"Reproducibility error ({error_nm:.3f} Nm) exceeds {ToleranceService.TOLERANCE_LIMITS['reproducibility_error_nm']} Nm limit"
                        )
                
                # Check output drive errors
                elif result.calculation_type == "output_drive":
                    error_nm = result.calculated_values.get("output_drive_error_nm", 0)
                    check_result["measurements"]["output_drive_error"] = error_nm
                    
                    if error_nm > ToleranceService.TOLERANCE_LIMITS["output_drive_error_nm"]:
                        check_result["passed"] = False
                        check_result["details"].append(
                            f"Output drive error ({error_nm:.3f} Nm) exceeds {ToleranceService.TOLERANCE_LIMITS['output_drive_error_nm']} Nm limit"
                        )
                
                # Check interface errors
                elif result.calculation_type == "interface":
                    error_nm = result.calculated_values.get("interface_error_nm", 0)
                    check_result["measurements"]["interface_error"] = error_nm
                    
                    if error_nm > ToleranceService.TOLERANCE_LIMITS["interface_error_nm"]:
                        check_result["passed"] = False
                        check_result["details"].append(
                            f"Interface error ({error_nm:.3f} Nm) exceeds {ToleranceService.TOLERANCE_LIMITS['interface_error_nm']} Nm limit"
                        )
                
                # Check loading point errors
                elif result.calculation_type == "loading_point":
                    error_nm = result.calculated_values.get("loading_point_error_nm", 0)
                    check_result["measurements"]["loading_point_error"] = error_nm
                    
                    if error_nm > ToleranceService.TOLERANCE_LIMITS["loading_point_error_nm"]:
                        check_result["passed"] = False
                        check_result["details"].append(
                            f"Loading point error ({error_nm:.3f} Nm) exceeds {ToleranceService.TOLERANCE_LIMITS['loading_point_error_nm']} Nm limit"
                        )
        
        return check_result
    
    @staticmethod
    def _check_uncertainty_limits(db: Session, job_id: int) -> Dict[str, Any]:
        """Check uncertainty calculations against tolerance limits"""
        check_result = {
            "check_type": "uncertainty_limits",
            "check_name": "Uncertainty Budget Validation",
            "passed": True,
            "severity": "MEDIUM",
            "details": [],
            "measurements": {},
            "recommendation": "Uncertainty within acceptable limits"
        }
        
        # Get uncertainty calculations
        uncertainty_calcs = db.query(UncertaintyCalculation).filter(
            UncertaintyCalculation.job_id == job_id
        ).all()
        
        for calc in uncertainty_calcs:
            # Check expanded uncertainty
            if calc.expanded_uncertainty_percent:
                expanded_unc = float(calc.expanded_uncertainty_percent)
                check_result["measurements"][f"expanded_uncertainty_{calc.set_torque}"] = expanded_unc
                
                if expanded_unc > ToleranceService.TOLERANCE_LIMITS["expanded_uncertainty_percent"]:
                    check_result["passed"] = False
                    check_result["severity"] = "HIGH"
                    check_result["details"].append(
                        f"Expanded uncertainty ({expanded_unc:.3f}%) exceeds {ToleranceService.TOLERANCE_LIMITS['expanded_uncertainty_percent']}% limit for {calc.set_torque} Nm"
                    )
                    check_result["recommendation"] = "Review measurement procedure and uncertainty sources"
            
            # Check combined uncertainty
            if calc.combined_uncertainty:
                combined_unc = float(calc.combined_uncertainty)
                check_result["measurements"][f"combined_uncertainty_{calc.set_torque}"] = combined_unc
                
                if combined_unc > ToleranceService.TOLERANCE_LIMITS["combined_uncertainty_limit"]:
                    check_result["passed"] = False
                    check_result["details"].append(
                        f"Combined uncertainty ({combined_unc:.3f}%) exceeds {ToleranceService.TOLERANCE_LIMITS['combined_uncertainty_limit']}% limit"
                    )
        
        return check_result
    
    @staticmethod
    def _check_measurement_errors(db: Session, job_id: int) -> Dict[str, Any]:
        """Check measurement errors from calculation results"""
        check_result = {
            "check_type": "measurement_errors",
            "check_name": "Measurement Error Analysis",
            "passed": True,
            "severity": "LOW",
            "details": [],
            "measurements": {},
            "recommendation": "Measurement errors within acceptable range"
        }
        
        # Get calculation results for measurement errors
        calc_results = db.query(JobCalculationResult).filter(
            JobCalculationResult.job_id == job_id,
            JobCalculationResult.calculation_type == "un_resolution_analysis"
        ).all()
        
        for result in calc_results:
            if result.calculated_values and "average_relative_error" in result.calculated_values:
                avg_error = abs(result.calculated_values["average_relative_error"])
                check_result["measurements"]["average_measurement_error"] = avg_error
                
                if avg_error > ToleranceService.TOLERANCE_LIMITS["measurement_error_limit"]:
                    check_result["passed"] = False
                    check_result["severity"] = "HIGH"
                    check_result["details"].append(
                        f"Average measurement error ({avg_error:.3f}%) exceeds {ToleranceService.TOLERANCE_LIMITS['measurement_error_limit']}% limit"
                    )
                    check_result["recommendation"] = "Review calibration procedure and reference standards"
        
        return check_result
    
    @staticmethod
    def _check_standards_validity(db: Session, job_id: int) -> Dict[str, Any]:
        """Check validity of standards used in calibration"""
        check_result = {
            "check_type": "standards_validity",
            "check_name": "Reference Standards Validation",
            "passed": True,
            "severity": "HIGH",
            "details": [],
            "measurements": {},
            "recommendation": "All reference standards are valid"
        }
        
        from app.models.jobs import Job
        from app.models.job_standards import JobStandard
        from app.models.standards import Standard
        from datetime import date
        
        # Get job and associated standards
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return check_result
        
        job_standards = db.query(JobStandard).filter(JobStandard.job_id == job_id).all()
        
        for job_standard in job_standards:
            standard = db.query(Standard).filter(Standard.id == job_standard.standard_id).first()
            if standard:
                # Check if standard is expired
                if standard.calibration_valid_upto < date.today():
                    check_result["passed"] = False
                    check_result["details"].append(
                        f"Standard '{standard.nomenclature}' expired on {standard.calibration_valid_upto}"
                    )
                    check_result["recommendation"] = "Replace expired standards before proceeding"
                
                # Check if standard is marked as inactive
                if not standard.is_active:
                    check_result["passed"] = False
                    check_result["details"].append(
                        f"Standard '{standard.nomenclature}' is marked as inactive"
                    )
        
        return check_result