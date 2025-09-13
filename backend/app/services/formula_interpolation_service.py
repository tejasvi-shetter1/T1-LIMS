# app/services/formula_interpolation_service.py
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import json
import logging

from app.models.calculations import FormulaLookupTable, StandardsCertificateData

logger = logging.getLogger(__name__)

class FormulaInterpolationService:
    """
    Excel XLOOKUP equivalent service for interpolating values from lookup tables
    
    Implements exact interpolation logic from Excel Formula sheet
    """

    def __init__(self, db: Session):
        self.db = db
        self._lookup_cache = {}

    def interpolate_torque_error(self, torque_value: float) -> float:
        """
        Interpolate torque error using INTERPOLATION lookup table
        
        From Excel: Based on torque value, find lower and higher range,
        then interpolate between error values
        """
        
        try:
            # Get interpolation lookup table
            lookup_table = self._get_lookup_table("interpolation", "torque_transducer")
            if not lookup_table:
                logger.warning("Interpolation lookup table not found, using default value")
                return 0.0
            
            # Handle lookup_data safely
            lookup_data = lookup_table.lookup_data
            if isinstance(lookup_data, str):
                try:
                    lookup_data = json.loads(lookup_data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in lookup_data")
                    return 0.0
            
            # Handle both list and dict formats for lookup_data
            if isinstance(lookup_data, dict):
                # Convert dict to list format if needed
                if "data" in lookup_data:
                    lookup_data = lookup_data["data"]
                elif "values" in lookup_data:
                    lookup_data = lookup_data["values"]
                else:
                    # Try to convert dict keys/values to list format
                    lookup_data = [{"torque_value": float(k), "interpolation_error": float(v)} 
                                 for k, v in lookup_data.items() if str(k).replace('.','').isdigit()]
            
            if not isinstance(lookup_data, list):
                logger.error(f"lookup_data is not a list after conversion, got {type(lookup_data)}")
                return 0.0
            
            # Validate data structure
            if not lookup_data:
                logger.warning("Empty lookup_data")
                return 0.0
            
            # Check if first row has expected keys
            if not isinstance(lookup_data[0], dict) or "torque_value" not in lookup_data[0]:
                logger.error("Invalid lookup_data structure")
                return 0.0
            
            # Find the appropriate interpolation point
            for row in lookup_data:
                if abs(row["torque_value"] - torque_value) < 0.1:  # Close match
                    return row.get("interpolation_error", 0.0)
            
            # If no exact match, perform linear interpolation
            return self._linear_interpolate(lookup_data, torque_value, "torque_value", "interpolation_error")
            
        except Exception as e:
            logger.error(f"Torque error interpolation failed: {e}")
            return 0.0

    def get_master_transducer_uncertainty(self, set_torque: float) -> float:
        """
        Get master transducer uncertainty from lookup table
        
        From Excel: Master Transducer Uncertainty / 2 table
        """
        
        try:
            lookup_table = self._get_lookup_table("uncertainty", "master_standard")
            if not lookup_table:
                logger.warning("Master transducer uncertainty lookup table not found, using default value")
                return 0.5  # Default uncertainty value

            lookup_data = lookup_table.lookup_data
            if isinstance(lookup_data, str):
                try:
                    lookup_data = json.loads(lookup_data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in master transducer lookup_data")
                    return 0.5
            
            if not isinstance(lookup_data, list) or not lookup_data:
                logger.warning("Invalid or empty master transducer lookup_data")
                return 0.5

            for row in lookup_data:
                if isinstance(row, dict) and "set_torque" in row and row["set_torque"] >= set_torque:
                    return row.get("uncertainty", 0.5)
            
            # Return last value if no match found
            if lookup_data and isinstance(lookup_data[-1], dict):
                return lookup_data[-1].get("uncertainty", 0.5)
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Master transducer uncertainty lookup failed: {e}")
            return 0.5

    def get_pressure_gauge_uncertainty(self, set_torque: float) -> float:
        """
        Get pressure gauge uncertainty based on set torque
        
        From Excel: Pressure gauge uncertainty lookup
        """
        
        try:
            lookup_table = self._get_lookup_table("pressure_uncertainty", "pressure_gauge")
            if not lookup_table:
                return 0.0
            
            # Complex calculation from Excel
            # δS un=(((AR5/2)*(D23/B23))/set_torque)
            ar5 = 0.390  # From Excel - pressure gauge uncertainty %
            d23 = 7190   # Max torque value from New RD
            b23 = 690    # Max pressure value from New RD
            
            return ((ar5 / 2) * (d23 / b23)) / set_torque
            
        except Exception as e:
            logger.error(f"Pressure gauge uncertainty calculation failed: {e}")
            return 0.0

    def get_cmc_value(self, torque_point: float) -> float:
        """
        Get CMC (Calibration and Measurement Capability) value
        
        From Excel: CMC lookup table with range-based values
        """
        
        try:
            lookup_table = self._get_lookup_table("cmc", "calibration_capability")
            if not lookup_table:
                logger.warning("CMC lookup table not found, using default value")
                return 2.0  # Default CMC value
            
            lookup_data = lookup_table.lookup_data
            if isinstance(lookup_data, str):
                try:
                    lookup_data = json.loads(lookup_data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in CMC lookup_data")
                    return 2.0
            
            if not isinstance(lookup_data, list) or not lookup_data:
                logger.warning("Invalid or empty CMC lookup_data")
                return 2.0
            
            # Find the range that contains this torque point
            for row in lookup_data:
                if isinstance(row, dict) and "lower_range" in row and "higher_range" in row:
                    if row["lower_range"] <= torque_point <= row["higher_range"]:
                        return row.get("cmc_percent", 2.0)
            
            return 2.0
            
        except Exception as e:
            logger.error(f"CMC value lookup failed: {e}")
            return 2.0

    def get_measurement_error(self, torque_point: float) -> float:
        """
        Get measurement error of the calibration device
        
        From Excel: Measurement error lookup table
        """
        
        try:
            lookup_table = self._get_lookup_table("measurement_error", "device_error")
            if not lookup_table:
                logger.warning("Measurement error lookup table not found, using default value")
                return 0.1  # Default measurement error
            
            lookup_data = lookup_table.lookup_data
            if isinstance(lookup_data, str):
                try:
                    lookup_data = json.loads(lookup_data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in measurement error lookup_data")
                    return 0.1
            
            if not isinstance(lookup_data, list) or not lookup_data:
                logger.warning("Invalid or empty measurement error lookup_data")
                return 0.1
            
            # Find matching range
            for row in lookup_data:
                if isinstance(row, dict) and "range_min" in row and "range_max" in row:
                    if row["range_min"] <= torque_point <= row["range_max"]:
                        return row.get("error_percent", 0.1)
            
            return 0.1
            
        except Exception as e:
            logger.error(f"Measurement error lookup failed: {e}")
            return 0.1

    def interpolate_certificate_data(self, standard_id: int, applied_torque: float) -> Dict[str, float]:
        """
        Interpolate certificate calibration data for a standard
        
        From Excel: Certificate validity tables with applied vs indicated torque
        """
        
        try:
            cert_data = self.db.query(StandardsCertificateData).filter(
                StandardsCertificateData.standard_id == standard_id,
                StandardsCertificateData.is_active == True
            ).first()
            
            if not cert_data:
                return {"indicated_torque": applied_torque, "error": 0.0, "uncertainty": 0.0}
            
            calibration_points = cert_data.calibration_points
            
            # Find closest calibration points for interpolation
            for point in calibration_points:
                if abs(point["applied_torque"] - applied_torque) < 0.1:
                    return {
                        "indicated_torque": point["indicated_torque"],
                        "error": point["error"],
                        "uncertainty": point["uncertainty"]
                    }
            
            # Linear interpolation between two closest points
            return self._interpolate_certificate_points(calibration_points, applied_torque)
            
        except Exception as e:
            logger.error(f"Certificate data interpolation failed: {e}")
            return {"indicated_torque": applied_torque, "error": 0.0, "uncertainty": 0.0}

    def _get_lookup_table(self, lookup_type: str, category: str) -> Optional[FormulaLookupTable]:
        """Get lookup table from database with caching"""
        
        cache_key = f"{lookup_type}_{category}"
        if cache_key in self._lookup_cache:
            return self._lookup_cache[cache_key]
        
        table = self.db.query(FormulaLookupTable).filter(
            FormulaLookupTable.lookup_type == lookup_type,
            FormulaLookupTable.category == category,
            FormulaLookupTable.is_active == True
        ).first()
        
        self._lookup_cache[cache_key] = table
        return table

    def _linear_interpolate(self, data: List[Dict], x_value: float, x_key: str, y_key: str) -> float:
        """Perform linear interpolation between data points"""
        
        # Sort data by x_key
        sorted_data = sorted(data, key=lambda item: item[x_key])
        
        # Handle edge cases
        if x_value <= sorted_data[0][x_key]:
            return sorted_data[0][y_key]
        if x_value >= sorted_data[-1][x_key]:
            return sorted_data[-1][y_key]
        
        # Find interpolation points
        for i in range(len(sorted_data) - 1):
            x1, y1 = sorted_data[i][x_key], sorted_data[i][y_key]
            x2, y2 = sorted_data[i + 1][x_key], sorted_data[i + 1][y_key]
            
            if x1 <= x_value <= x2:
                # Linear interpolation formula: y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                return y1 + (y2 - y1) * (x_value - x1) / (x2 - x1)
        
        return 0.0

    def _interpolate_certificate_points(self, calibration_points: List[Dict], applied_torque: float) -> Dict[str, float]:
        """Interpolate between certificate calibration points"""
        
        # Sort by applied torque
        sorted_points = sorted(calibration_points, key=lambda p: p["applied_torque"])
        
        # Find interpolation bounds
        for i in range(len(sorted_points) - 1):
            point1 = sorted_points[i]
            point2 = sorted_points[i + 1]
            
            if point1["applied_torque"] <= applied_torque <= point2["applied_torque"]:
                # Interpolate each field
                ratio = (applied_torque - point1["applied_torque"]) / (point2["applied_torque"] - point1["applied_torque"])
                
                return {
                    "indicated_torque": point1["indicated_torque"] + ratio * (point2["indicated_torque"] - point1["indicated_torque"]),
                    "error": point1["error"] + ratio * (point2["error"] - point1["error"]),
                    "uncertainty": point1["uncertainty"] + ratio * (point2["uncertainty"] - point1["uncertainty"])
                }
        
        # Return closest point if no interpolation possible
        closest_point = min(sorted_points, key=lambda p: abs(p["applied_torque"] - applied_torque))
        return {
            "indicated_torque": closest_point["indicated_torque"],
            "error": closest_point["error"],
            "uncertainty": closest_point["uncertainty"]
        }
