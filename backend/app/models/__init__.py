# app/models/__init__.py (CORRECTED)
from .base import TimestampMixin, SoftDeleteMixin, AuditMixin
from .customers import Customer
from .users import User, UserRole, UserType
from .equipment import EquipmentCategory, EquipmentType, CalculationFormula  # REMOVED StandardsSelectionRule
from .srf import SRF, SRFItem
from .inward import Inward
from .jobs import Job, JobStatus
from .measurements import Measurement, UncertaintyCalculation, MeasurementTemplate
from .standards import Standard, JobStandard, StandardsSelectionRule  # MOVED StandardsSelectionRule HERE
from .deviations import DeviationReport, DeviationStatus
from .certificates import Certificate, CertificateStatus, CertificateType, CertificateTemplate, GenerationStatus

# NEW: Calculation Engine Models
from .calculations import (
    FormulaLookupTable, 
    CalculationMethod, 
    JobCalculationResult, 
    StandardsCertificateData, 
    CalculationEngineConfig,
    CalculationStage,
    CalculationStatus
)

__all__ = [
    "TimestampMixin", "SoftDeleteMixin", "AuditMixin",
    "Customer", "User", "UserRole", "UserType",
    "EquipmentCategory", "EquipmentType", "CalculationFormula",  # REMOVED StandardsSelectionRule
    "SRF", "SRFItem",
    "Inward",
    "Job", "JobStatus",
    "Measurement", "UncertaintyCalculation", "MeasurementTemplate",
    "Standard", "JobStandard", "StandardsSelectionRule",  # MOVED StandardsSelectionRule HERE
    "DeviationReport", "DeviationStatus", 
    "Certificate", "CertificateStatus", "CertificateType", "CertificateTemplate", "GenerationStatus",
    
    # NEW: Calculation Engine Models
    "FormulaLookupTable", 
    "CalculationMethod", 
    "JobCalculationResult", 
    "StandardsCertificateData", 
    "CalculationEngineConfig",
    "CalculationStage",
    "CalculationStatus"
]
