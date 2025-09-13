# app/services/auto_deviation_service.py - Enhanced Auto Deviation Detection Service
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.models.deviations import DeviationReport
from app.models.jobs import Job
from app.models.customers import Customer
from app.services.tolerance_service import ToleranceService

logger = logging.getLogger(__name__)

class AutoDeviationService:
    """
    Enhanced Auto-Deviation Detection Service
    
    Integrates with ToleranceService to automatically create deviation reports
    when tolerance checks fail.
    """
    
    @staticmethod
    def auto_generate_deviation_reports(
        db: Session, 
        job_id: int, 
        current_user: str = "AUTO_CALCULATION_ENGINE"
    ) -> List[DeviationReport]:
        """
        🚨 Auto-generate deviation reports based on tolerance check failures
        """
        # Run tolerance checks
        tolerance_results = ToleranceService.check_job_tolerances(db, job_id)
        generated_deviations = []
        
        # Only generate deviations if required
        if not tolerance_results["deviation_required"]:
            logger.info(f"No deviations required for job {job_id}")
            return generated_deviations
        
        # Generate deviation for each failed check
        for failure in tolerance_results["failures"]:
            deviation_data = AutoDeviationService._create_deviation_from_failure(
                job_id, failure, tolerance_results["severity"], current_user
            )
            
            deviation = AutoDeviationService._create_deviation_record(db, deviation_data)
            generated_deviations.append(deviation)
            logger.info(f"Auto-generated deviation {deviation.deviation_number} for job {job_id}")
        
        # Generate summary deviation if multiple failures
        if len(tolerance_results["failures"]) > 1:
            summary_deviation = AutoDeviationService._create_summary_deviation(
                job_id, tolerance_results, current_user
            )
            deviation = AutoDeviationService._create_deviation_record(db, summary_deviation)
            generated_deviations.append(deviation)
        
        return generated_deviations
    
    @staticmethod
    def _create_deviation_from_failure(job_id: int, failure: Dict, severity: str, current_user: str) -> Dict[str, Any]:
        """Create deviation data from tolerance check failure"""
        
        # Map failure types to deviation types
        deviation_type_mapping = {
            "environmental_conditions": "ENVIRONMENTAL",
            "calculation_tolerances": "OOT",  # Out of Tolerance
            "uncertainty_limits": "OOT",
            "measurement_errors": "GB_FAILURE",  # Go/Bad Failure
            "standards_validity": "STANDARDS_EXPIRED"
        }
        
        deviation_type = deviation_type_mapping.get(failure["check_type"], "OOT")
        
        # Create comprehensive description
        description = f"""AUTOMATED DEVIATION REPORT

Check Type: {failure['check_name']}
Severity: {severity}

Details:
{chr(10).join(f"• {detail}" for detail in failure['details'])}

Measurements:
{chr(10).join(f"• {key}: {value}" for key, value in failure.get('measurements', {}).items())}

Recommendation: {failure['recommendation']}

This deviation was automatically generated based on tolerance check failures.
""".strip()
        
        # Determine technical and customer impact
        technical_impact = AutoDeviationService._assess_technical_impact(failure, severity)
        customer_impact = AutoDeviationService._assess_customer_impact(failure, severity)
        
        return {
            "job_id": job_id,
            "deviation_type": deviation_type,
            "severity": severity.lower(),
            "description": description,
            "technical_impact": technical_impact,
            "customer_impact": customer_impact,
            "identified_by": current_user,
            "affected_measurements": failure.get('measurements', {}),
            "recommendations": [failure['recommendation']]
        }
    
    @staticmethod
    def _create_summary_deviation(job_id: int, tolerance_results: Dict, current_user: str) -> Dict[str, Any]:
        """Create summary deviation for multiple failures"""
        
        description = f"""COMPREHENSIVE CALIBRATION DEVIATION REPORT

Multiple tolerance violations detected during calibration process.

Summary:
• Total Checks: {tolerance_results['summary']['total_checks']}
• Failed Checks: {tolerance_results['summary']['failed_checks']}
• Warning Checks: {tolerance_results['summary']['warning_checks']}
• Pass Rate: {tolerance_results['summary']['pass_rate']:.1f}%

Failed Checks:
{chr(10).join([f"• {f['check_name']}: {', '.join(f['details'])}" for f in tolerance_results['failures']])}

Overall Assessment: REQUIRES CUSTOMER APPROVAL for certificate issuance.
"""
        
        return {
            "job_id": job_id,
            "deviation_type": "OOT",
            "severity": tolerance_results["severity"].lower(),
            "description": description,
            "technical_impact": "Multiple calibration parameters outside acceptable limits",
            "customer_impact": "Certificate may require special conditions or re-calibration",
            "identified_by": current_user,
            "affected_measurements": {"multiple_failures": len(tolerance_results["failures"])},
            "recommendations": ["Review all failed tolerance checks", "Consider re-calibration", "Consult with customer"]
        }
    
    @staticmethod
    def _create_deviation_record(db: Session, deviation_data: Dict[str, Any]) -> DeviationReport:
        """Create deviation record in database"""
        
        try:
            # Generate deviation number
            deviation_number = AutoDeviationService._generate_deviation_number(db, deviation_data["job_id"])
            
            # Create deviation report
            deviation = DeviationReport(
                job_id=deviation_data["job_id"],
                deviation_number=deviation_number,
                deviation_type=deviation_data["deviation_type"],
                severity=deviation_data["severity"],
                description=deviation_data["description"],
                technical_impact=deviation_data["technical_impact"],
                customer_impact=deviation_data["customer_impact"],
                recommendations="\n".join(deviation_data.get("recommendations", [])),
                status="open",
                identified_by=deviation_data["identified_by"],
                created_at=datetime.now(),
                affected_measurements=deviation_data.get("affected_measurements", {})
            )
            
            db.add(deviation)
            db.commit()
            
            return deviation
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create deviation record: {e}")
            raise
    
    @staticmethod
    def _generate_deviation_number(db: Session, job_id: int) -> str:
        """Generate unique deviation number"""
        
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        
        # Count existing deviations for this job
        existing_count = db.query(DeviationReport).filter(
            DeviationReport.job_id == job_id
        ).count()
        
        # Generate deviation number: DEV-{NEPL_WORK_ID}-{SEQUENCE}
        nepl_work_id = job.nepl_work_id if job else f"JOB{job_id}"
        sequence = existing_count + 1
        
        return f"DEV-{nepl_work_id}-{sequence:03d}"
    
    @staticmethod
    def _assess_technical_impact(failure: Dict, severity: str) -> str:
        """Assess technical impact of failure"""
        
        impact_mapping = {
            "environmental_conditions": "Environmental conditions outside acceptable limits affect measurement validity and traceability",
            "calculation_tolerances": "Calculation results exceed tolerance limits affecting measurement accuracy",
            "uncertainty_limits": "Measurement uncertainty exceeds acceptable limits affecting result reliability",
            "measurement_errors": "Systematic measurement errors detected affecting calibration accuracy",
            "standards_validity": "Reference standards expired or invalid affecting traceability"
        }
        
        base_impact = impact_mapping.get(failure["check_type"], "Technical parameters outside acceptable limits")
        
        if severity == "HIGH":
            return f"CRITICAL: {base_impact}. Immediate corrective action required."
        elif severity == "MEDIUM":
            return f"MODERATE: {base_impact}. Review and corrective action recommended."
        else:
            return f"MINOR: {base_impact}. Monitoring and documentation required."
    
    @staticmethod
    def _assess_customer_impact(failure: Dict, severity: str) -> str:
        """Assess customer impact of failure"""
        
        if severity == "HIGH":
            return "Certificate may require conditional acceptance, re-calibration, or special customer approval"
        elif severity == "MEDIUM":
            return "Certificate can be issued with noted limitations and customer notification"
        else:
            return "Minimal customer impact - certificate can be issued with documentation"