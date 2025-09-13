# scripts/test_realistic_data.py - Test with realistic laboratory data
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

def test_realistic_calibration():
    """Test with realistic calibration data showing typical laboratory performance"""
    
    db = SessionLocal()
    try:
        calc_service = CalculationEngineService(db)
        
        # Create realistic measurement data (typical ±2% repeatability)
        measurement_data = create_realistic_measurement_data()
        
        print("🧪 TESTING WITH REALISTIC LABORATORY DATA")
        print("=" * 60)
        print("📋 Test Scenario: Typical hydraulic torque wrench calibration")
        print("🎯 Expected: Good repeatability (±2%), low uncertainty")
        print()
        
        # Execute workflow
        result = calc_service.execute_complete_calculation_workflow(
            job_id=2,  # Different job ID
            measurement_data=measurement_data,
            config_name="hydraulic_torque_wrench_standard"
        )
        
        # Print results
        print("🧪 REALISTIC CALIBRATION TEST RESULTS")
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
                                    print(f"      Max deviation: {calc_result['max_deviation']:.3f}%")
                            else:
                                print(f"    - {calc_type}: ❌ {calc_result['error']}")
                        else:
                            # Handle non-dict results (like floats)
                            print(f"    - {calc_type}: ✅")
        
        deviation_count = len(result.get('deviation_reports', []))
        if deviation_count == 0:
            print("✅ No deviations detected - EXCELLENT!")
        else:
            print(f"⚠️ {deviation_count} deviations detected")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
        
        print("\n�� DETAILED ANALYSIS:")
        final_results = result.get('final_results', {})
        if final_results:
            calc_summary = final_results.get('calculation_summary', {})
            print(f"All Stages Successful: {calc_summary.get('all_stages_successful', False)}")
            
            # Show measurement results
            measurement_results = final_results.get('measurement_results', {})
            if measurement_results:
                print("\n📏 MEASUREMENT PERFORMANCE:")
                repeatability = measurement_results.get('repeatability', {})
                max_dev = repeatability.get('max_deviation_percent', 0)
                
                # Evaluate performance
                if abs(max_dev) <= 2.0:
                    performance = "🟢 EXCELLENT"
                elif abs(max_dev) <= 4.0:
                    performance = "🟡 GOOD"
                else:
                    performance = "🔴 REQUIRES ATTENTION"
                
                print(f"  Max Repeatability Deviation: {max_dev:.3f}% {performance}")
                print(f"  Reproducibility Error: {measurement_results.get('reproducibility_error_nm', 0):.3f} Nm")
                print(f"  Output Drive Error: {measurement_results.get('output_drive_error_nm', 0):.3f} Nm")
                print(f"  Interface Error: {measurement_results.get('interface_error_nm', 0):.3f} Nm")
                print(f"  Loading Point Error: {measurement_results.get('loading_point_error_nm', 0):.3f} Nm")
            
            # Show uncertainty results
            uncertainty_results = final_results.get('uncertainty_results', {})
            if uncertainty_results:
                print("\n🎯 UNCERTAINTY ANALYSIS:")
                max_unc = uncertainty_results.get('max_expanded_uncertainty_percent', 0)
                
                # Evaluate uncertainty
                if max_unc <= 0.5:
                    unc_performance = "🟢 OUTSTANDING"
                elif max_unc <= 1.0:
                    unc_performance = "🟡 VERY GOOD"
                elif max_unc <= 2.0:
                    unc_performance = "🟠 ACCEPTABLE"
                else:
                    unc_performance = "🔴 NEEDS IMPROVEMENT"
                
                print(f"  Max Expanded Uncertainty: {max_unc:.3f}% {unc_performance}")
                print(f"  Average Expanded Uncertainty: {uncertainty_results.get('average_expanded_uncertainty_percent', 0):.3f}%")
                print(f"  Within ISO Limits (5%): {uncertainty_results.get('within_iso_limits', False)}")
                print(f"  Within Lab Limits (3%): {uncertainty_results.get('within_typical_lab_limits', False)}")
            
            # Show validation summary
            validation_summary = final_results.get('validation_summary', {})
            if validation_summary:
                print(f"\n✅ COMPLIANCE STATUS:")
                print(f"  ISO 6789 Compliant: {validation_summary.get('iso_compliant', False)}")
                print(f"  Requires Deviation Report: {validation_summary.get('requires_deviation_report', False)}")
                
                if not validation_summary.get('requires_deviation_report', True):
                    print("  🎉 CALIBRATION PASSED - Ready for certificate issuance!")
                else:
                    print("  📋 Deviation report required - Review measurement conditions")
        
        # Compare with previous extreme test
        print(f"\n📊 COMPARISON WITH EXTREME TEST CASE:")
        print(f"  Previous Max Deviation: -15.61% (Extreme case)")
        print(f"  Current Max Deviation: {final_results.get('measurement_results', {}).get('repeatability', {}).get('max_deviation_percent', 0):.3f}% (Realistic case)")
        print(f"  Improvement: {abs(-15.61 - final_results.get('measurement_results', {}).get('repeatability', {}).get('max_deviation_percent', 0)):.1f} percentage points")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def create_realistic_measurement_data() -> Dict[str, Any]:
    """Create realistic measurement data showing typical laboratory performance"""
    
    return {
        "repeatability_points": [
            {
                "set_torque": 1349,
                "readings": [1335, 1338, 1342, 1340, 1337],  # ±0.5% variation (realistic)
                "pressure": 138
            },
            {
                "set_torque": 4269,
                "readings": [4245, 4250, 4255, 4248, 4252],  # ±0.3% variation (excellent)
                "pressure": 414
            },
            {
                "set_torque": 7190,
                "readings": [7165, 7170, 7175, 7168, 7172],  # ±0.2% variation (outstanding)
                "pressure": 690
            }
        ],
        "reproducibility": {
            "set_torque": 1349,
            "sequences": {
                "I": [1336.2, 1337.1, 1338.0, 1337.5, 1336.8],  # Tight grouping
                "II": [1337.8, 1338.2, 1337.9, 1338.1, 1337.6],
                "III": [1338.5, 1338.8, 1338.2, 1338.6, 1338.3],
                "IV": [1337.2, 1337.6, 1337.4, 1337.8, 1337.1]
            }
        },
        "output_drive": {
            "set_torque": 1349,
            "positions": {
                "0°": [1337, 1338, 1339, 1337, 1338, 1339, 1337, 1338, 1339, 1338],    # Consistent
                "90°": [1336, 1337, 1338, 1336, 1337, 1338, 1336, 1337, 1338, 1337],   # Slightly lower
                "180°": [1338, 1339, 1340, 1338, 1339, 1340, 1338, 1339, 1340, 1339],  # Slightly higher
                "270°": [1337, 1338, 1339, 1337, 1338, 1339, 1337, 1338, 1339, 1338]   # Consistent
            }
        },
        "interface": {
            "set_torque": 1349,
            "positions": {
                "0°": [1338, 1339, 1340, 1338, 1339, 1340, 1338, 1339, 1340, 1339],
                "90°": [1337, 1338, 1339, 1337, 1338, 1339, 1337, 1338, 1339, 1338],
                "180°": [1339, 1340, 1341, 1339, 1340, 1341, 1339, 1340, 1341, 1340],
                "270°": [1338, 1339, 1340, 1338, 1339, 1340, 1338, 1339, 1340, 1339]
            }
        },
        "loading_point": {
            "set_torque": 1349,
            "-10mm": [1336.5, 1337.2, 1336.8, 1337.0],  # Small variation
            "+10mm": [1338.2, 1337.8, 1338.0, 1337.9]   # Small difference
        }
    }

def test_both_scenarios():
    """Test both extreme and realistic scenarios for comparison"""
    print("🔬 COMPREHENSIVE CALIBRATION ENGINE TESTING")
    print("=" * 60)
    
    print("\n1️⃣ TESTING EXTREME CASE (from actual certificate):")
    print("   - High repeatability deviation (-15.61%)")
    print("   - Requires deviation report")
    print("   - Demonstrates system handles edge cases")
    
    # Run original extreme test
    os.system("python test_calculation_engine.py")
    
    print("\n" + "="*60)
    print("\n2️⃣ TESTING REALISTIC CASE (typical laboratory performance):")
    print("   - Expected good repeatability (±2%)")
    print("   - Should pass without deviations")
    print("   - Demonstrates normal operation")
    
    # Run realistic test
    test_realistic_calibration()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "both":
        test_both_scenarios()
    else:
        test_realistic_calibration()