import numpy as np
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.measurements import Measurement, UncertaintyCalculation, MeasurementType
from app.schemas.measurements import MeasurementCreate, RepeatabilityData, ReproducibilityData


class MeasurementService:
    
    @staticmethod
    def create_repeatability_measurement(
        db: Session,
        job_id: int,
        measurement_data: RepeatabilityData,
        current_user: str = "system"
    ) -> Measurement:
        """
        Create repeatability measurement (Type A - 5 readings per point)
        Exact implementation from Excel "New Format RD" sheet
        """
        
        # Process measurement data exactly as in Excel
        processed_data = MeasurementService._process_repeatability_data(measurement_data)
        
        # Create measurement record
        measurement = Measurement(
            job_id=job_id,
            measurement_type=MeasurementType.REPEATABILITY,
            measurement_plan_name="ISO 6789-1 Repeatability Test",
            calibration_date=measurement_data.calibration_date,
            temp_before=measurement_data.temp_before,
            temp_after=measurement_data.temp_after,
            humidity_before=measurement_data.humidity_before,
            humidity_after=measurement_data.humidity_after,
            measurement_data=processed_data,
            technician=current_user,
            created_by=current_user
        )
        
        db.add(measurement)
        db.flush()
        
        # Calculate uncertainties for each measurement point
        for point_data in processed_data["measurement_points"]:
            uncertainty_calc = MeasurementService._calculate_repeatability_uncertainty(
                measurement.id,
                point_data["set_torque"],
                point_data["readings"],
                point_data["statistics"]
            )
            db.add(uncertainty_calc)
        
        measurement.is_completed = True
        db.commit()
        db.refresh(measurement)
        
        return measurement
    
    @staticmethod
    def _process_repeatability_data(measurement_data: RepeatabilityData) -> Dict:
        """
        Process repeatability data exactly as Excel does
        
        From Excel: Steps 20%, 60%, 100% with 5 readings each
        Example: Set Torque 1349 Nm → Readings: 1225, 1225, 1226, 1224, 1225
        """
        processed_points = []
        
        for point in measurement_data.measurement_points:
            # CORRECT - Use dot notation for Pydantic models
            set_torque = point.set_torque
            readings = point.readings  # 5 readings: S1, S2, S3, S4, S5
            set_pressure = point.set_pressure or 0  # Pressure gauge reading
            
            # Calculate statistics exactly as Excel
            mean_value = np.mean(readings)
            std_dev = np.std(readings, ddof=1)  # Sample standard deviation
            
            # Corrected standard (Excel: mean of deviations)
            corrected_standard = np.mean([abs(r - mean_value) for r in readings])
            
            # Corrected mean (Excel formula)
            corrected_mean = mean_value - corrected_standard
            
            # Deviation (Excel: max deviation)
            max_deviation = max([abs(r - mean_value) for r in readings])
            
            # Variation due to repeatability (Excel formula)
            # From UN_resolution sheet: bre = std_dev / sqrt(5)
            repeatability_variation = std_dev / np.sqrt(len(readings))
            
            processed_point = {
                "set_torque": float(set_torque),
                "set_pressure": float(set_pressure),
                "readings": readings,
                "statistics": {
                    "mean": float(mean_value),
                    "std_dev": float(std_dev),
                    "corrected_standard": float(corrected_standard),
                    "corrected_mean": float(corrected_mean),
                    "max_deviation": float(max_deviation),
                    "repeatability_variation": float(repeatability_variation)
                }
            }
            processed_points.append(processed_point)
        
        return {
            "measurement_type": "repeatability",
            "measurement_points": processed_points,
            "summary": {
                "total_points": len(processed_points),
                "readings_per_point": 5
            }
        }
    
    @staticmethod
    def _process_reproducibility_data(measurement_data: ReproducibilityData) -> Dict:
        """
        Process reproducibility data exactly as Excel
        """
        
        #  CORRECT - Use dot notation
        series_data = measurement_data.series_measurements
        set_torque = measurement_data.set_torque
        
        # Calculate mean for each series
        series_means = []
        for series in series_data:
            # CORRECT - Access dictionary keys for series data
            series_mean = np.mean(series.measurements)  # Use dot notation for Pydantic model
            series_means.append(series_mean)
        
        # Calculate overall mean
        overall_mean = np.mean(series_means)
        
        # Calculate reproducibility error (max - min of series means)
        reproducibility_error = max(series_means) - min(series_means)
        
        # Relative reproducibility error
        relative_error = (reproducibility_error / set_torque) * 100
        
        return {
            "measurement_type": "reproducibility",
            "set_torque": float(set_torque),
            "series_data": [
                {
                    "series_number": i + 1,
                    "measurements": series.measurements,  #  Use dot notation
                    "mean": float(series_means[i])
                }
                for i, series in enumerate(series_data)
            ],
            "overall_mean": float(overall_mean),
            "reproducibility_error": float(reproducibility_error),
            "relative_error_percent": float(relative_error)
        }
    
    @staticmethod
    def create_reproducibility_measurement(
        db: Session,
        job_id: int,
        measurement_data: ReproducibilityData,
        current_user: str = "system"
    ) -> Measurement:
        """
        Create reproducibility measurement (Type B - 4 sequences)
        From Excel: Series I, II, III, IV with 5 measurements each
        """
        
        processed_data = MeasurementService._process_reproducibility_data(measurement_data)
        
        measurement = Measurement(
            job_id=job_id,
            measurement_type=MeasurementType.REPRODUCIBILITY,
            measurement_plan_name="ISO 6789-1 Reproducibility Test",
            calibration_date=measurement_data.calibration_date,
            measurement_data=processed_data,
            technician=current_user,
            created_by=current_user
        )
        
        db.add(measurement)
        db.flush()
        
        # Calculate reproducibility uncertainty
        reproducibility_error = processed_data["reproducibility_error"]
        uncertainty_calc = UncertaintyCalculation(
            measurement_id=measurement.id,
            set_torque=measurement_data.set_torque,
            uncertainty_reproducibility=Decimal(str(reproducibility_error / (2 * np.sqrt(3)))),  # Type B rectangular
            created_by=current_user
        )
        db.add(uncertainty_calc)
        
        measurement.is_completed = True
        db.commit()
        db.refresh(measurement)
        
        return measurement
    
    @staticmethod
    def create_output_drive_measurement(
        db: Session,
        job_id: int,
        measurement_data: dict,
        current_user: str = "system"
    ) -> Measurement:
        """
        Create output drive geometric effect measurement
        From Excel: 4 positions (0°, 90°, 180°, 270°) with 10 measurements each
        """
        
        processed_data = MeasurementService._process_output_drive_data(measurement_data)
        
        measurement = Measurement(
            job_id=job_id,
            measurement_type=MeasurementType.OUTPUT_DRIVE,
            measurement_plan_name="ISO 6789-1 Output Drive Geometric Effect",
            calibration_date=measurement_data["calibration_date"],
            measurement_data=processed_data,
            technician=current_user,
            created_by=current_user
        )
        
        db.add(measurement)
        db.flush()
        
        # Calculate output drive uncertainty
        output_drive_error = processed_data["output_drive_error"]
        uncertainty_calc = UncertaintyCalculation(
            measurement_id=measurement.id,
            set_torque=measurement_data["set_torque"],
            uncertainty_output_drive=Decimal(str(output_drive_error / (2 * np.sqrt(3)))),  # Type B rectangular
            created_by=current_user
        )
        db.add(uncertainty_calc)
        
        measurement.is_completed = True
        db.commit()
        db.refresh(measurement)
        
        return measurement
    
    @staticmethod
    def _process_output_drive_data(measurement_data: dict) -> Dict:
        """
        Process output drive geometric effect data
        
        From Excel Crt2 sheet:
        Position 0°: Mean 1225.2
        Position 90°: Mean 1224.8  
        Position 180°: Mean 1225.2
        Position 270°: Mean 1225.3
        Error due to output drive: 0.5 Nm
        """
        
        position_data = measurement_data["position_measurements"]
        set_torque = measurement_data["set_torque"]
        
        # Calculate mean for each position
        position_means = []
        processed_positions = []
        
        for position in position_data:
            position_mean = np.mean(position["measurements"])
            position_means.append(position_mean)
            
            processed_positions.append({
                "position": position["position"],  # "0°", "90°", etc.
                "measurements": position["measurements"],
                "mean": float(position_mean)
            })
        
        # Calculate output drive error (max - min of position means)
        output_drive_error = max(position_means) - min(position_means)
        
        # Relative error
        relative_error = (output_drive_error / set_torque) * 100
        
        return {
            "measurement_type": "output_drive",
            "set_torque": float(set_torque),
            "position_data": processed_positions,
            "output_drive_error": float(output_drive_error),
            "relative_error_percent": float(relative_error)
        }
    
    @staticmethod
    def _calculate_repeatability_uncertainty(
        measurement_id: int,
        set_torque: float,
        readings: List[float],
        statistics: Dict
    ) -> UncertaintyCalculation:
        """
        Calculate uncertainty for repeatability measurement
        Using exact Excel formulas from Uncertainty sheet
        """
        
        # Type A uncertainty (repeatability)
        # From Excel: brep = std_dev / sqrt(n) where n = number of readings
        repeatability_uncertainty = statistics["std_dev"] / np.sqrt(len(readings))
        
        # For Type A, divide by 2*sqrt(5) for rectangular distribution
        type_a_uncertainty = repeatability_uncertainty / (2 * np.sqrt(5))
        
        return UncertaintyCalculation(
            measurement_id=measurement_id,
            set_torque=Decimal(str(set_torque)),
            uncertainty_repeatability=Decimal(str(type_a_uncertainty)),
            created_by="system"
        )