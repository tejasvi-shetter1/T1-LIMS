# scripts/seed_formula_lookup_tables.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.calculations import FormulaLookupTable, CalculationEngineConfig
import json
from datetime import datetime

def seed_interpolation_lookup_table():
    """Seed INTERPOLATION lookup table from Excel data"""
    db = SessionLocal()
    
    try:
        # Interpolation table data from Excel
        interpolation_data = {
            "table_name": "torque_interpolation_1500_40000",
            "equipment_type_id": 1,  # Hydraulic torque wrench
            "lookup_type": "interpolation",
            "category": "torque_transducer",
            "range_column": "torque_value",
            "validity_period": "23-11-2024 / 13-03-2026",
            "data_structure": {
                "columns": {
                    "torque_value": "float",
                    "lower_range": "float", 
                    "higher_range": "float",
                    "error_lower": "float",
                    "error_higher": "float",
                    "interpolation_error": "float"
                }
            },
            "lookup_data": [
                {
                    "torque_value": 1225.0,
                    "lower_range": 900.0,
                    "higher_range": 1500.0,
                    "error_lower": -2.0,
                    "error_higher": -1.0,
                    "interpolation_error": 1.458333333333333
                },
                {
                    "torque_value": 3602.8,
                    "lower_range": 1500.0,
                    "higher_range": 5000.0,
                    "error_lower": -1.0,
                    "error_higher": 0.0,
                    "interpolation_error": 0.3992
                },
                {
                    "torque_value": 6352.8,
                    "lower_range": 5000.0,
                    "higher_range": 10000.0,
                    "error_lower": 0.0,
                    "error_higher": 3.0,
                    "interpolation_error": 0.81168
                }
            ]
        }
        
        lookup_table = FormulaLookupTable(**interpolation_data)
        db.add(lookup_table)
        
        print("✅ Interpolation lookup table seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding interpolation table: {e}")
    finally:
        db.close()

def seed_master_transducer_uncertainty():
    """Seed Master Transducer Uncertainty / 2 lookup table"""
    db = SessionLocal()
    
    try:
        uncertainty_data = {
            "table_name": "master_transducer_uncertainty",
            "equipment_type_id": 1,
            "lookup_type": "uncertainty",
            "category": "master_standard",
            "range_column": "set_torque",
            "data_structure": {
                "columns": {
                    "set_torque": "float",
                    "higher_value": "float", 
                    "uncertainty": "float",
                    "uncertainty_half": "float"
                }
            },
            "lookup_data": [
                {
                    "set_torque": 1349.0,
                    "higher_value": 1503.58,
                    "uncertainty": 0.16,
                    "uncertainty_half": 0.08
                },
                {
                    "set_torque": 4269.0,
                    "higher_value": 5000.0,
                    "uncertainty": 0.05,
                    "uncertainty_half": 0.025
                },
                {
                    "set_torque": 7190.0,
                    "higher_value": 9997.0,
                    "uncertainty": 0.04,
                    "uncertainty_half": 0.02
                }
            ]
        }
        
        lookup_table = FormulaLookupTable(**uncertainty_data)
        db.add(lookup_table)
        
        print("✅ Master transducer uncertainty table seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding uncertainty table: {e}")
    finally:
        db.close()

def seed_cmc_lookup_table():
    """Seed CMC lookup table from Excel"""
    db = SessionLocal()
    
    try:
        cmc_data = {
            "table_name": "cmc_scope_hydraulic",
            "equipment_type_id": 1,
            "lookup_type": "cmc",
            "category": "calibration_capability",
            "range_column": "torque_point",
            "data_structure": {
                "columns": {
                    "torque_point": "float",
                    "std_cmc": "float",
                    "lower_range": "float",
                    "higher_range": "float",
                    "cmc_percent": "float"
                }
            },
            "lookup_data": [
                {
                    "torque_point": 1349,
                    "std_cmc": 0.58,
                    "lower_range": 200,
                    "higher_range": 1500,
                    "cmc_percent": 0.58
                },
                {
                    "torque_point": 4269,
                    "std_cmc": 0.37,
                    "lower_range": 1500,
                    "higher_range": 5000,
                    "cmc_percent": 0.37
                },
                {
                    "torque_point": 7190,
                    "std_cmc": 0.49,
                    "lower_range": 5000,
                    "higher_range": 10000,
                    "cmc_percent": 0.49
                },
                {
                    "torque_point": 12500,
                    "std_cmc": 0.52,
                    "lower_range": 10000,
                    "higher_range": 20000,
                    "cmc_percent": 0.52
                },
                {
                    "torque_point": 27500,
                    "std_cmc": 0.53,
                    "lower_range": 20000,
                    "higher_range": 35000,
                    "cmc_percent": 0.53
                }
            ]
        }
        
        lookup_table = FormulaLookupTable(**cmc_data)
        db.add(lookup_table)
        
        print("✅ CMC lookup table seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding CMC table: {e}")
    finally:
        db.close()

def seed_pressure_gauge_uncertainty():
    """Seed pressure gauge uncertainty table"""
    db = SessionLocal()
    
    try:
        pressure_data = {
            "table_name": "pressure_gauge_mass_0_1000_bar",
            "equipment_type_id": 1,
            "lookup_type": "pressure_uncertainty",
            "category": "pressure_gauge",
            "range_column": "set_pressure",
            "validity_period": "Certificate Validity: MASS 0-1000 bar",
            "data_structure": {
                "columns": {
                    "uncertainty_percent": "float",
                    "set_pressure_low": "float",
                    "set_pressure_high": "float"
                }
            },
            "lookup_data": [
                {"uncertainty_percent": 0.39, "set_pressure_low": 70, "set_pressure_high": 138},
                {"uncertainty_percent": 0.39, "set_pressure_low": 210, "set_pressure_high": 276},
                {"uncertainty_percent": 0.39, "set_pressure_low": 420, "set_pressure_high": 414},
                {"uncertainty_percent": 0.39, "set_pressure_low": 560, "set_pressure_high": 552},
                {"uncertainty_percent": 0.39, "set_pressure_low": 700, "set_pressure_high": 690}
            ]
        }
        
        lookup_table = FormulaLookupTable(**pressure_data)
        db.add(lookup_table)
        
        print("✅ Pressure gauge uncertainty table seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding pressure gauge table: {e}")
    finally:
        db.close()

def seed_measurement_error_table():
    """Seed measurement error table"""
    db = SessionLocal()
    
    try:
        measurement_error_data = {
            "table_name": "measurement_error_calibration_device",
            "equipment_type_id": 1,
            "lookup_type": "measurement_error",
            "category": "device_error",
            "range_column": "torque_point",
            "data_structure": {
                "columns": {
                    "torque_point": "float",
                    "error_percent": "float",
                    "range_min": "float",
                    "range_max": "float",
                    "uncertainty_percent": "float"
                }
            },
            "lookup_data": [
                {
                    "torque_point": 1349,
                    "error_percent": 0.15,
                    "range_min": 100,
                    "range_max": 1500,
                    "uncertainty_percent": 0.15
                },
                {
                    "torque_point": 4269,
                    "error_percent": 0.16,
                    "range_min": 1501,
                    "range_max": 35000,
                    "uncertainty_percent": 0.16
                },
                {
                    "torque_point": 7190,
                    "error_percent": 0.16,
                    "range_min": 1501,
                    "range_max": 35000,
                    "uncertainty_percent": 0.16
                }
            ]
        }
        
        lookup_table = FormulaLookupTable(**measurement_error_data)
        db.add(lookup_table)
        
        print("✅ Measurement error table seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding measurement error table: {e}")
    finally:
        db.close()

def seed_calculation_engine_config():
    """Seed calculation engine configuration"""
    db = SessionLocal()
    
    try:
        config_data = {
            "config_name": "hydraulic_torque_wrench_standard",
            "equipment_type": "torque",
            "stage1_methods": {
                "repeatability": {
                    "order": 1,
                    "required_readings": 5,
                    "calculation_points": [{"percentage": 20}, {"percentage": 60}, {"percentage": 100}],
                    "formulas": {
                        "mean": "AVERAGE(readings)",
                        "corrected_standard": "INTERPOLATE(mean_value, interpolation_table)",
                        "corrected_mean": "mean - corrected_standard",
                        "deviation_percent": "((corrected_mean - set_torque) * 100) / set_torque"
                    },
                    "tolerance_limits": {"max_deviation_percent": 4.0}
                },
                "reproducibility": {
                    "order": 2,
                    "required_sequences": 4,
                    "readings_per_sequence": 5,
                    "formulas": {
                        "series_means": "AVERAGE each series",
                        "reproducibility_error": "MAX(series_means) - MIN(series_means)"
                    }
                },
                "output_drive": {
                    "order": 3,
                    "positions": ["0°", "90°", "180°", "270°"],
                    "readings_per_position": 10,
                    "formulas": {
                        "position_means": "AVERAGE each position",
                        "output_drive_error": "MAX(position_means) - MIN(position_means)"
                    }
                },
                "interface": {
                    "order": 4,
                    "positions": ["0°", "90°", "180°", "270°"],
                    "readings_per_position": 10,
                    "formulas": {
                        "position_means": "AVERAGE each position", 
                        "interface_error": "MAX(position_means) - MIN(position_means)"
                    }
                },
                "loading_point": {
                    "order": 5,
                    "positions": ["-10mm", "+10mm"],
                    "readings_per_position": 5,
                    "formulas": {
                        "position_means": "AVERAGE each position",
                        "loading_point_error": "ABS(position1_mean - position2_mean)"
                    }
                }
            },
            "stage2_methods": {
                "un_resolution_repeatability": {
                    "order": 1,
                    "inputs": ["target_values", "reference_values"],
                    "formulas": {
                        "measurement_error": "target_value - reference_value",
                        "relative_error": "(measurement_error * 100) / reference_value",
                        "corrected_mean": "AVERAGE(reference_values) - corrected_standard",
                        "deviation": "reference_value - corrected_mean",
                        "repeatability_variation": "STDEV(deviations)"
                    }
                }
            },
            "stage3_methods": {
                "uncertainty_budget": {
                    "order": 1,
                    "components": [
                        "uncertainty_pressure_gauge",
                        "resolution_input_pressure", 
                        "uncertainty_standard",
                        "uncertainty_resolution",
                        "uncertainty_reproducibility",
                        "uncertainty_output_drive",
                        "uncertainty_interface",
                        "uncertainty_loading_point",
                        "uncertainty_repeatability"
                    ],
                    "formulas": {
                        "combined_uncertainty": "SQRT(sum of squares of all components)",
                        "expanded_uncertainty_percent": "combined_uncertainty * coverage_factor",
                        "expanded_uncertainty_absolute": "(expanded_uncertainty_percent * set_torque) / 100"
                    }
                }
            },
            "auto_deviation_enabled": True,
            "tolerance_config": {
                "repeatability_max_deviation": 4.0,
                "uncertainty_max_percent": 3.0,
                "environmental_temp_min": 20.0,
                "environmental_temp_max": 30.0,
                "environmental_humidity_min": 60.0,
                "environmental_humidity_max": 70.0
            },
            "notification_config": {
                "email_enabled": True,
                "email_template": "auto_deviation_notification",
                "escalation_hours": 24
            },
            "formula_constants": {
                "coverage_factor": 2.0,
                "sqrt_3": 1.732050808,
                "sqrt_5": 2.236067977
            }
        }
        
        engine_config = CalculationEngineConfig(**config_data)
        db.add(engine_config)
        
        print("✅ Calculation engine configuration seeded")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding engine config: {e}")
    finally:
        db.close()

def run_all_seeds():
    """Run all seeding functions"""
    print("🌱 Starting formula lookup tables seeding...")
    
    seed_interpolation_lookup_table()
    seed_master_transducer_uncertainty()
    seed_cmc_lookup_table()
    seed_pressure_gauge_uncertainty()
    seed_measurement_error_table()
    seed_calculation_engine_config()
    
    print("✅ All formula lookup tables seeded successfully!")

if __name__ == "__main__":
    run_all_seeds()
