# test_calculation_engine.py - UPDATED VERSION
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.calculation_engine_service import CalculationEngineService
import json
from typing import Dict, Any

# Database setup
DATABASE_URL: str = "postgresql://postgres:Aimlsn%402025@localhost/nepl_lims_local"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_calculation_engine():
    """Test the calculation engine with properly structured data"""
    
    db = SessionLocal()
    try:
        calc_service = CalculationEngineService(db)
        
        # Create properly structured test data
        measurement_data = create_test_measurement_data()
        
        # Execute workflow
        result = calc_service.execute_complete_calculation_workflow(
            job_id=1,
            measurement_data=measurement_data,
            config_name="hydraulic_torque_wrench_standard"
        )
        
        # Print results
        print("🧪 CALCULATION ENGINE TEST RESULTS")
        print("=" * 50)
        print(f"✅ Workflow Success: {result['success']}")
        
        if result.get('stage_results'):
            print("📊 Stages Completed:")
            for stage, stage_result in result['stage_results'].items():
                status = "✅" if stage_result.get('success') else "❌"
                print(f"  {stage}: {status}")
                
                # Print detailed results for each calculation
                if stage_result.get('success') and 'calculations' in stage_result:
                    print(f"  {stage} detailed results:")
                    for calc_type, calc_result in stage_result['calculations'].items():
                        # Handle both dict and non-dict results
                        if isinstance(calc_result, dict):
                            if 'error' not in calc_result:
                                print(f"    - {calc_type}: ✅")
                                if calc_type == 'repeatability' and 'max_deviation' in calc_result:
                                    print(f"      Max deviation: {calc_result['max_deviation']:.2f}%")
                            else:
                                print(f"    - {calc_type}: ❌ {calc_result['error']}")
                        else:
                            # Handle non-dict results (like floats)
                            print(f"    - {calc_type}: ✅")
        
        deviation_count = len(result.get('deviation_reports', []))
        if deviation_count == 0:
            print("✅ No deviations detected")
        else:
            print(f"⚠️ {deviation_count} deviations detected")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
        
        print("\n🔍 SUMMARY:")
        final_results = result.get('final_results', {})
        if final_results:
            calc_summary = final_results.get('calculation_summary', {})
            print(f"Stage 1 Completed: {calc_summary.get('stage1_completed', False)}")
            print(f"Stage 2 Completed: {calc_summary.get('stage2_completed', False)}")
            print(f"Stage 3 Completed: {calc_summary.get('stage3_completed', False)}")
            print(f"All Stages Successful: {calc_summary.get('all_stages_successful', False)}")
            
            # Show measurement results
            measurement_results = final_results.get('measurement_results', {})
            if measurement_results:
                print("\n📏 MEASUREMENT RESULTS:")
                repeatability = measurement_results.get('repeatability', {})
                print(f"  Max Repeatability Deviation: {repeatability.get('max_deviation_percent', 0):.3f}%")
                print(f"  Reproducibility Error: {measurement_results.get('reproducibility_error_nm', 0):.3f} Nm")
                print(f"  Output Drive Error: {measurement_results.get('output_drive_error_nm', 0):.3f} Nm")
                print(f"  Interface Error: {measurement_results.get('interface_error_nm', 0):.3f} Nm")
                print(f"  Loading Point Error: {measurement_results.get('loading_point_error_nm', 0):.3f} Nm")
            
            # Show uncertainty results
            uncertainty_results = final_results.get('uncertainty_results', {})
            if uncertainty_results:
                print("\n🎯 UNCERTAINTY RESULTS:")
                print(f"  Max Expanded Uncertainty: {uncertainty_results.get('max_expanded_uncertainty_percent', 0):.3f}%")
                print(f"  Min Expanded Uncertainty: {uncertainty_results.get('min_expanded_uncertainty_percent', 0):.3f}%")
                print(f"  Average Expanded Uncertainty: {uncertainty_results.get('average_expanded_uncertainty_percent', 0):.3f}%")
                print(f"  Within ISO Limits: {uncertainty_results.get('within_iso_limits', False)}")
                print(f"  Within Lab Limits: {uncertainty_results.get('within_typical_lab_limits', False)}")
            
            # Show validation summary
            validation_summary = final_results.get('validation_summary', {})
            if validation_summary:
                print(f"\n✅ VALIDATION:")
                print(f"  Stage 1 Validation: {validation_summary.get('stage1_validation', 'unknown')}")
                print(f"  ISO Compliant: {validation_summary.get('iso_compliant', False)}")
                print(f"  Requires Deviation Report: {validation_summary.get('requires_deviation_report', False)}")
        else:
            print("No final results available")
        
        # Show summary from workflow
        summary = result.get('summary', {})
        if summary:
            print(f"\n⏱️ EXECUTION SUMMARY:")
            print(f"  Execution Time: {summary.get('execution_time', 'N/A')}")
            print(f"  Stages Completed: {summary.get('stages_completed', 0)}/{summary.get('total_stages', 3)}")
            print(f"  Overall Status: {summary.get('overall_status', 'unknown')}")
            
            key_metrics = summary.get('key_metrics', {})
            if key_metrics:
                print(f"  Max Expanded Uncertainty: {key_metrics.get('max_expanded_uncertainty', 'N/A')}")
                print(f"  Max Repeatability Deviation: {key_metrics.get('max_repeatability_deviation', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def create_test_measurement_data() -> Dict[str, Any]:
    """Create properly structured test measurement data based on Excel format"""
    
    return {
        "repeatability_points": [
            {
                "set_torque": 1349,
                "readings": [1225, 1225, 1226, 1224, 1225],
                "pressure": 138
            },
            {
                "set_torque": 4269,
                "readings": [3605, 3604, 3604, 3597, 3604],
                "pressure": 414
            },
            {
                "set_torque": 7190,
                "readings": [6350, 6346, 6353, 6354, 6361],
                "pressure": 690
            }
        ],
        "reproducibility": {
            "set_torque": 1349,
            "sequences": {
                "I": [1225.99, 1224.55, 1225.41, 1225.58, 1225.16],
                "II": [1224.86, 1224.54, 1224.58, 1224.83, 1225.01],
                "III": [1224.42, 1224.02, 1224.26, 1225.20, 1225.95],
                "IV": [1225.45, 1224.93, 1225.05, 1224.99, 1224.99]
            }
        },
        "output_drive": {
            "set_torque": 1349,
            "positions": {
                "0°": [1225, 1226, 1226, 1224, 1225, 1225, 1225, 1225, 1225, 1226],
                "90°": [1225, 1226, 1225, 1225, 1226, 1224, 1226, 1224, 1225, 1224],
                "180°": [1226, 1225, 1224, 1224, 1226, 1224, 1226, 1224, 1224, 1224],
                "270°": [1225, 1226, 1224, 1226, 1226, 1226, 1226, 1224, 1226, 1225]
            }
        },
        "interface": {
            "set_torque": 1349,
            "positions": {
                "0°": [1226, 1224, 1226, 1226, 1225, 1225, 1225, 1224, 1226, 1225],
                "90°": [1225, 1226, 1224, 1226, 1225, 1225, 1224, 1224, 1224, 1225],
                "180°": [1225, 1225, 1226, 1226, 1226, 1225, 1225, 1224, 1226, 1224],
                "270°": [1226, 1224, 1225, 1226, 1226, 1226, 1226, 1225, 1225, 1224]
            }
        },
        "loading_point": {
            "set_torque": 1349,
            "-10mm": [1220.04, 1222.76, 1223.04, 1223.34],
            "+10mm": [1223.68, 1222.20, 1223.96, 1222.68]
        }
    }

if __name__ == "__main__":
    test_calculation_engine()
