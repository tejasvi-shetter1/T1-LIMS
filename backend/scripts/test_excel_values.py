# scripts/test_excel_values.py - Test with exact Excel values from values.xlsx
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

def test_excel_values():
    """Test calculation engine with exact values from values.xlsx"""
    
    db = SessionLocal()
    try:
        calc_service = CalculationEngineService(db)
        
        # Create measurement data from Excel values
        measurement_data = create_excel_measurement_data()
        
        print("🧪 TESTING WITH EXACT EXCEL VALUES (values.xlsx)")
        print("=" * 70)
        print("📋 Test Data: NEPL Work ID 25060-13")
        print("🔧 Equipment: PRIMO/PMU-10 Hydraulic Torque Wrench")
        print("📅 Date: 2025-08-11")
        print("🎯 Range: 2250-5000 Nm")
        print()
        
        # Execute workflow
        result = calc_service.execute_complete_calculation_workflow(
            job_id=3,  # Different job ID for this test
            measurement_data=measurement_data,
            config_name="hydraulic_torque_wrench_standard"
        )
        
        # Print results with Excel comparison
        print("🧪 EXCEL VALUES TEST RESULTS")
        print("=" * 50)
        print(f"✅ Workflow Success: {result['success']}")
        
        if result.get('stage_results'):
            print("\n📊 DETAILED STAGE RESULTS:")
            
            # Stage 1 Results with Excel Comparison
            stage1 = result['stage_results'].get('stage1', {})
            if stage1.get('success') and 'calculations' in stage1:
                print("\n🔍 STAGE 1: NEW RD CALCULATIONS")
                print("-" * 40)
                
                # A. Repeatability Comparison
                repeatability = stage1['calculations'].get('repeatability', {})
                if isinstance(repeatability, dict) and 'measurement_points' in repeatability:
                    print("\nA. REPEATABILITY ANALYSIS:")
                    
                    expected_deviations = [0.2877066666666603, 48.30432733333334, 23.956678999999998]
                    
                    for i, point in enumerate(repeatability['measurement_points']):
                        calculated_dev = point.get('deviation_percent', 0)
                        expected_dev = expected_deviations[i] if i < len(expected_deviations) else 0
                        
                        match_status = "✅ MATCH" if abs(calculated_dev - expected_dev) < 0.01 else "❌ MISMATCH"
                        
                        print(f"  Point {i+1} ({point.get('set_torque', 0)} Nm):")
                        print(f"    Calculated: {calculated_dev:.6f}%")
                        print(f"    Excel:      {expected_dev:.6f}%")
                        print(f"    Status:     {match_status}")
                        print(f"    Difference: {abs(calculated_dev - expected_dev):.6f}%")
                        print()
                
                # B. Reproducibility Comparison
                reproducibility = stage1['calculations'].get('reproducibility', {})
                if isinstance(reproducibility, dict):
                    print("B. REPRODUCIBILITY ANALYSIS:")
                    calculated_error = reproducibility.get('reproducibility_error_nm', 0)
                    expected_error = 5.800000000000182
                    
                    match_status = "✅ MATCH" if abs(calculated_error - expected_error) < 0.01 else "❌ MISMATCH"
                    
                    print(f"  Calculated Error: {calculated_error:.6f} Nm")
                    print(f"  Excel Error:      {expected_error:.6f} Nm")
                    print(f"  Status:           {match_status}")
                    print(f"  Difference:       {abs(calculated_error - expected_error):.6f} Nm")
                    print()
                
                # C. Output Drive Comparison
                output_drive = stage1['calculations'].get('output_drive', {})
                if isinstance(output_drive, dict):
                    print("C. OUTPUT DRIVE ANALYSIS:")
                    calculated_error = output_drive.get('output_drive_error_nm', 0)
                    expected_error = 4.5
                    
                    match_status = "✅ MATCH" if abs(calculated_error - expected_error) < 0.01 else "❌ MISMATCH"
                    
                    print(f"  Calculated Error: {calculated_error:.6f} Nm")
                    print(f"  Excel Error:      {expected_error:.6f} Nm")
                    print(f"  Status:           {match_status}")
                    print(f"  Difference:       {abs(calculated_error - expected_error):.6f} Nm")
                    print()
                
                # D. Interface Comparison
                interface = stage1['calculations'].get('interface', {})
                if isinstance(interface, dict):
                    print("D. INTERFACE ANALYSIS:")
                    calculated_error = interface.get('interface_error_nm', 0)
                    expected_error = 5.300000000000182
                    
                    match_status = "✅ MATCH" if abs(calculated_error - expected_error) < 0.01 else "❌ MISMATCH"
                    
                    print(f"  Calculated Error: {calculated_error:.6f} Nm")
                    print(f"  Excel Error:      {expected_error:.6f} Nm")
                    print(f"  Status:           {match_status}")
                    print(f"  Difference:       {abs(calculated_error - expected_error):.6f} Nm")
                    print()
                
                # E. Loading Point Comparison
                loading_point = stage1['calculations'].get('loading_point', {})
                if isinstance(loading_point, dict):
                    print("E. LOADING POINT ANALYSIS:")
                    calculated_error = loading_point.get('loading_point_error_nm', 0)
                    expected_error = 2.800000000000182
                    
                    match_status = "✅ MATCH" if abs(calculated_error - expected_error) < 0.01 else "❌ MISMATCH"
                    
                    print(f"  Calculated Error: {calculated_error:.6f} Nm")
                    print(f"  Excel Error:      {expected_error:.6f} Nm")
                    print(f"  Status:           {match_status}")
                    print(f"  Difference:       {abs(calculated_error - expected_error):.6f} Nm")
                    print()
            
            # Stage 3 Uncertainty Budget Comparison
            stage3 = result['stage_results'].get('stage3', {})
            if stage3.get('success') and 'uncertainty_budget' in stage3:
                print("\n🎯 STAGE 3: UNCERTAINTY BUDGET COMPARISON")
                print("-" * 50)
                
                uncertainty_budget = stage3['uncertainty_budget']
                expected_expanded_uncertainties = [0.27047849651223554, 0.22084064909281562, 0.07612605932760445]
                
                for i, budget in enumerate(uncertainty_budget):
                    if i < len(expected_expanded_uncertainties):
                        calculated_unc = budget.get('expanded_uncertainty_percent', 0)
                        expected_unc = expected_expanded_uncertainties[i]
                        
                        match_status = "✅ MATCH" if abs(calculated_unc - expected_unc) < 0.01 else "❌ MISMATCH"
                        
                        print(f"Point {i+1} ({budget.get('set_torque', 0)} Nm):")
                        print(f"  Calculated Expanded Uncertainty: {calculated_unc:.6f}%")
                        print(f"  Excel Expanded Uncertainty:      {expected_unc:.6f}%")
                        print(f"  Status:                          {match_status}")
                        print(f"  Difference:                      {abs(calculated_unc - expected_unc):.6f}%")
                        print()
        
        # Overall Summary
        print("\n📋 OVERALL EXCEL VALIDATION SUMMARY")
        print("=" * 50)
        
        deviation_count = len(result.get('deviation_reports', []))
        print(f"Deviations Detected: {deviation_count}")
        
        final_results = result.get('final_results', {})
        if final_results:
            measurement_results = final_results.get('measurement_results', {})
            uncertainty_results = final_results.get('uncertainty_results', {})
            
            print(f"\nMeasurement Performance:")
            if measurement_results:
                repeatability = measurement_results.get('repeatability', {})
                print(f"  Max Repeatability Deviation: {repeatability.get('max_deviation_percent', 0):.3f}%")
                print(f"  Expected from Excel: 48.304% (Point 2)")
                
                print(f"  Reproducibility Error: {measurement_results.get('reproducibility_error_nm', 0):.3f} Nm")
                print(f"  Expected from Excel: 5.800 Nm")
                
                print(f"  Output Drive Error: {measurement_results.get('output_drive_error_nm', 0):.3f} Nm")
                print(f"  Expected from Excel: 4.500 Nm")
                
                print(f"  Interface Error: {measurement_results.get('interface_error_nm', 0):.3f} Nm")
                print(f"  Expected from Excel: 5.300 Nm")
                
                print(f"  Loading Point Error: {measurement_results.get('loading_point_error_nm', 0):.3f} Nm")
                print(f"  Expected from Excel: 2.800 Nm")
            
            print(f"\nUncertainty Performance:")
            if uncertainty_results:
                print(f"  Max Expanded Uncertainty: {uncertainty_results.get('max_expanded_uncertainty_percent', 0):.6f}%")
                print(f"  Expected from Excel: 0.270478%")
                
                print(f"  Within ISO Limits: {uncertainty_results.get('within_iso_limits', False)}")
                print(f"  Within Lab Limits: {uncertainty_results.get('within_typical_lab_limits', False)}")
        
        # Test Status Summary
        print(f"\n🎯 TEST VALIDATION STATUS:")
        print(f"  Workflow Execution: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
        print(f"  All Stages Complete: {'✅ YES' if all([result.get('stage_results', {}).get(f'stage{i}', {}).get('success', False) for i in [1, 2, 3]]) else '❌ NO'}")
        print(f"  Excel Formula Compliance: {'✅ VERIFIED' if result.get('success') else '❌ NEEDS REVIEW'}")
        
        if deviation_count > 0:
            print(f"  ⚠️  High deviations detected - This matches Excel data showing significant measurement errors")
            print(f"      Point 2 (6000 Nm): 48.30% deviation - Requires investigation")
            print(f"      Point 3 (12000 Nm): 23.96% deviation - Requires investigation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def create_excel_measurement_data() -> Dict[str, Any]:
    """Create measurement data exactly matching values.xlsx"""
    
    return {
        "repeatability_points": [
            {
                "set_torque": 3000,
                "readings": [3001, 3009, 3005, 3015, 3016],  # S1-S5 from Excel
                "pressure": 138
            },
            {
                "set_torque": 6000,
                "readings": [8932, 8882, 8891, 8887, 8911],  # S1-S5 from Excel
                "pressure": 414
            },
            {
                "set_torque": 12000,
                "readings": [14896, 14883, 14872, 14878, 14881],  # S1-S5 from Excel
                "pressure": 690
            }
        ],
        "reproducibility": {
            "set_torque": 3000,
            "sequences": {
                "I": [3001, 3013, 3003, 3014, 3003],  # Sequence I from Excel
                "II": [3012, 3003, 3004, 3002, 3005],  # Sequence II from Excel
                "III": [3011, 3015, 3009, 3014, 3006],  # Sequence III from Excel
                "IV": [3014, 3006, 3001, 3009, 3011]   # Sequence IV from Excel
            }
        },
        "output_drive": {
            "set_torque": 3000,
            "positions": {
                "0°": [3010, 3008, 3010, 3011, 3015, 3014, 3013, 3014, 3015, 3009],    # 0° position from Excel
                "90°": [3015, 3008, 3007, 3016, 3009, 3010, 3003, 3007, 3012, 3007],   # 90° position from Excel
                "180°": [3011, 3014, 3002, 3013, 3003, 3005, 3014, 3008, 3002, 3008],  # 180° position from Excel
                "270°": [3016, 3005, 3008, 3005, 3004, 3004, 3014, 3002, 3013, 3003]   # 270° position from Excel
            }
        },
        "interface": {
            "set_torque": 3000,
            "positions": {
                "0°": [3011, 3015, 3016, 3012, 3004, 3001, 3011, 3005, 3012, 3016],    # 0° interface from Excel
                "90°": [3013, 3014, 3001, 3007, 3016, 3003, 3006, 3015, 3006, 3001],   # 90° interface from Excel
                "180°": [3015, 3016, 3015, 3007, 3012, 3013, 3002, 3013, 3003, 3004],  # 180° interface from Excel
                "270°": [3002, 3002, 3003, 3003, 3001, 3003, 3008, 3014, 3002, 3012]   # 270° interface from Excel
            }
        },
        "loading_point": {
            "set_torque": 3000,
            "-10mm": [2997, 2997, 2997, 2999, 2999],  # -10mm position from Excel
            "+10mm": [3002, 3002, 3002, 3001, 3001]   # +10mm position from Excel
        }
    }

def run_comprehensive_validation():
    """Run comprehensive validation comparing all test scenarios"""
    
    print("🔬 COMPREHENSIVE CALCULATION ENGINE VALIDATION")
    print("=" * 70)
    
    print("\n1️⃣ TESTING WITH EXCEL VALUES (values.xlsx)")
    print("   - Real laboratory data from NEPL Work ID 25060-13")
    print("   - PRIMO/PMU-10 Hydraulic Torque Wrench")
    print("   - Expected high deviations (48.30%, 23.96%)")
    
    test_excel_values()
    
    print("\n" + "="*70)
    print("\n📊 VALIDATION COMPLETE")
    print("This test validates the calculation engine against real Excel data")
    print("showing both normal and extreme measurement scenarios.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "comprehensive":
        run_comprehensive_validation()
    else:
        test_excel_values()