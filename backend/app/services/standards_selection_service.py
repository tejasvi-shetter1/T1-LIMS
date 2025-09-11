from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date
import re
import logging

from app.models.standards import Standard, StandardsSelectionRule, JobStandard
from app.models.equipment import EquipmentType, EquipmentCategory
from app.models.jobs import Job

logger = logging.getLogger(__name__)

class StandardsSelectionService:
    
    @staticmethod
    def auto_select_standards_for_job(
        db: Session,
        job_id: int,
        equipment_desc: str,
        range_min: float,
        range_max: float,
        unit: str
    ) -> List[Dict[str, Any]]:
        """
        Auto-select standards for a job based on equipment and range
        """
        try:
            # Step 1: Identify equipment type
            equipment_type = StandardsSelectionService._identify_equipment_type(
                db, equipment_desc, range_min, range_max, unit
            )
            
            if not equipment_type:
                logger.warning(f"No equipment type found for: {equipment_desc}")
                return StandardsSelectionService._fallback_standards_selection(
                    db, equipment_desc, range_min, range_max, unit
                )
            
            # Step 2: Get active selection rules
            selection_rules = db.query(StandardsSelectionRule).filter(
                StandardsSelectionRule.equipment_type_id == equipment_type.id,
                StandardsSelectionRule.is_active == True
            ).order_by(StandardsSelectionRule.priority).all()
            
            # Step 3: Apply selection rules
            selected_standards = []
            
            if selection_rules:
                for rule in selection_rules:
                    matching_standards = StandardsSelectionService._apply_selection_rule(
                        db, rule, range_min, range_max, unit
                    )
                    
                    if matching_standards:
                        best_standard = matching_standards[0]
                        selected_standards.append({
                            'standard': best_standard,
                            'rule': rule,
                            'sequence': rule.priority,
                            'selection_reason': f"Auto-selected by rule: {rule.rule_name or 'Default rule'}"
                        })
            else:
                # Fallback to direct matching
                logger.info(f"No selection rules found for {equipment_type.nomenclature}, using fallback")
                fallback_standards = StandardsSelectionService._fallback_standards_selection(
                    db, equipment_desc, range_min, range_max, unit
                )
                selected_standards = fallback_standards
            
            return selected_standards
            
        except Exception as e:
            logger.error(f"Error in auto_select_standards_for_job: {e}")
            return StandardsSelectionService._fallback_standards_selection(
                db, equipment_desc, range_min, range_max, unit
            )
    
    @staticmethod
    def _identify_equipment_type(
        db: Session,
        equipment_desc: str,
        range_min: float,
        range_max: float,
        unit: str
    ) -> Optional[EquipmentType]:
        """
        Identify equipment type based on description and range
        """
        equipment_desc_upper = equipment_desc.upper()
        
        # Query equipment types with active status
        equipment_types = db.query(EquipmentType).filter(
            EquipmentType.is_active == True
        ).all()
        
        for eq_type in equipment_types:
            if not eq_type.nomenclature or not eq_type.unit:
                continue
                
            # Pattern matching logic
            nomenclature_words = eq_type.nomenclature.upper().split()
            
            # Check for keyword matches
            keyword_matches = sum(1 for word in nomenclature_words if word in equipment_desc_upper)
            
            if keyword_matches >= 1:  # At least one keyword match
                # Check unit compatibility
                if eq_type.unit.lower() == unit.lower():
                    # Check range compatibility
                    if (eq_type.min_range is None or range_min >= eq_type.min_range) and \
                       (eq_type.max_range is None or range_max <= eq_type.max_range):
                        return eq_type
        
        return None
    
    @staticmethod
    def _apply_selection_rule(
        db: Session,
        rule: StandardsSelectionRule,
        range_min: float,
        range_max: float,
        unit: str
    ) -> List[Standard]:
        """
        Apply a specific selection rule to find matching standards
        """
        query = db.query(Standard).filter(
            Standard.is_active == True,
            Standard.is_expired == False,
            Standard.calibration_valid_upto > date.today(),
            Standard.unit == unit
        )
        
        # Apply rule-specific filters
        if rule.standard_id:
            # Direct standard assignment
            query = query.filter(Standard.id == rule.standard_id)
        else:
            # Range-based matching
            if rule.range_min is not None and rule.range_max is not None:
                query = query.filter(
                    Standard.range_min <= rule.range_max,
                    Standard.range_max >= rule.range_min
                )
        
        standards = query.order_by(Standard.uncertainty).all()
        
        # Filter by actual device range coverage
        suitable_standards = []
        for standard in standards:
            if standard.range_min is not None and standard.range_max is not None:
                # Check if standard can measure the device range
                if float(standard.range_min) <= range_min and float(standard.range_max) >= range_max:
                    suitable_standards.append(standard)
        
        return suitable_standards
    
    @staticmethod
    def _fallback_standards_selection(
        db: Session,
        equipment_desc: str,
        range_min: float,
        range_max: float,
        unit: str
    ) -> List[Dict[str, Any]]:
        """
        Fallback standards selection when no specific rules exist
        """
        # Determine discipline from equipment description
        discipline = StandardsSelectionService._determine_discipline(equipment_desc)
        
        # Find standards by discipline and range
        standards = db.query(Standard).filter(
            Standard.is_active == True,
            Standard.is_expired == False,
            Standard.calibration_valid_upto > date.today(),
            Standard.unit == unit,
            Standard.discipline == discipline,
            Standard.range_min <= range_min,
            Standard.range_max >= range_max
        ).order_by(Standard.uncertainty).all()
        
        selected_standards = []
        for i, standard in enumerate(standards[:2]):  # Max 2 standards
            selected_standards.append({
                'standard': standard,
                'rule': None,
                'sequence': i + 1,
                'selection_reason': f"Fallback selection by discipline: {discipline}"
            })
        
        return selected_standards
    
    @staticmethod
    def _determine_discipline(equipment_desc: str) -> str:
        """
        Determine discipline from equipment description
        """
        desc_upper = equipment_desc.upper()
        
        if any(word in desc_upper for word in ['TORQUE', 'WRENCH', 'MULTIPLIER']):
            return 'Torque'
        elif any(word in desc_upper for word in ['PRESSURE', 'GAUGE', 'PUMP']):
            return 'Pressure'
        elif any(word in desc_upper for word in ['EARTH', 'TESTER', 'PHASE', 'VOLTAGE']):
            return 'Electrical'
        elif any(word in desc_upper for word in ['CALIPER', 'VERNIER', 'DIMENSION']):
            return 'Dimensional'
        else:
            return 'General'
    
    @staticmethod
    def create_job_standards(
        db: Session,
        job_id: int,
        selected_standards: List[Dict[str, Any]]
    ) -> List[JobStandard]:
        """
        Create JobStandard records for the selected standards
        """
        # Remove existing auto-selected standards for this job
        db.query(JobStandard).filter(
            JobStandard.job_id == job_id,
            JobStandard.auto_selected == True
        ).delete()
        
        job_standards = []
        
        for item in selected_standards:
            standard = item['standard']
            
            job_standard = JobStandard(
                job_id=job_id,
                standard_id=standard.id,
                standard_sequence=item['sequence'],
                is_primary=(item['sequence'] == 1),
                auto_selected=True,
                selection_reason=item['selection_reason'],
                usage_notes=f"Auto-selected based on equipment type and range"
            )
            
            db.add(job_standard)
            job_standards.append(job_standard)
        
        db.commit()
        return job_standards
    
    @staticmethod
    def get_available_standards_for_equipment(
        db: Session,
        equipment_desc: str,
        range_min: float,
        range_max: float,
        unit: str
    ) -> List[Dict[str, Any]]:
        """
        Get all available standards for manual selection
        """
        discipline = StandardsSelectionService._determine_discipline(equipment_desc)
        
        standards = db.query(Standard).filter(
            Standard.is_active == True,
            Standard.is_expired == False,
            Standard.calibration_valid_upto > date.today(),
            Standard.unit == unit
        ).all()
        
        available_standards = []
        
        for standard in standards:
            if standard.range_min is not None and standard.range_max is not None:
                # Calculate coverage
                overlap_min = max(range_min, float(standard.range_min))
                overlap_max = min(range_max, float(standard.range_max))
                
                if overlap_max > overlap_min:
                    coverage_ratio = (overlap_max - overlap_min) / (range_max - range_min)
                    
                    available_standards.append({
                        'standard': standard,
                        'coverage_ratio': coverage_ratio,
                        'is_optimal': coverage_ratio >= 0.8,
                        'validity_days': (standard.calibration_valid_upto - date.today()).days,
                        'discipline_match': standard.discipline == discipline
                    })
        
        # Sort by coverage ratio and discipline match
        available_standards.sort(
            key=lambda x: (x['discipline_match'], x['coverage_ratio']),
            reverse=True
        )
        
        return available_standards
