# scripts/test_phase2_apis.py - Test Phase 2 Enhanced APIs
import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_JOB_ID = 1

# Test data from Excel values
EXCEL_MEASUREMENT_DATA = {
    "repeatability_points": [
        {
            "set_torque": 3000,
            "readings": [3001, 3009, 3005, 3015, 3016],
            "pressure": 138
        },
        {
            "set_torque": 6000,
            "readings": [8932, 8882, 8891, 8887, 8911],
            "pressure": 414
        },
        {
            "set_torque": 12000,
            "readings": [14896, 14883, 14872, 14878, 14881],
            "pressure": 690
        }
    ],
    "reproducibility": {
        "set_torque": 3000,
        "sequences": {
            "I": [3001, 3013, 3003, 3014, 3003],
            "II": [3012, 3003, 3004, 3002, 3005],
            "III": [3011, 3015, 3009, 3014, 3006],
            "IV": [3014, 3006, 3001, 3009, 3011]
        }
    },
    "output_drive": {
        "set_torque": 3000,
        "positions": {
            "0°": [3010, 3008, 3010, 3011, 3015, 3014, 3013, 3014, 3015, 3009],
            "90°": [3015, 3008, 3007, 3016, 3009, 3010, 3003, 3007, 3012, 3007],
            "180°": [3011, 3014, 3002, 3013, 3003, 3005, 3014, 3008, 3002, 3008],
            "270°": [3016, 3005, 3008, 3005, 3004, 3004, 3014, 3002, 3013, 3003]
        }
    },
    "interface": {
        "set_torque": 3000,
        "positions": {
            "0°": [3011, 3015, 3016, 3012, 3004, 3001, 3011, 3005, 3012, 3016],
            "90°": [3013, 3014, 3001, 3007, 3016, 3003, 3006, 3015, 3006, 3001],
            "180°": [3015, 3016, 3015, 3007, 3012, 3013, 3002, 3013, 3003, 3004],
            "270°": [3002, 3002, 3003, 3003, 3001, 3003, 3008, 3014, 3002, 3012]
        }
    },
    "loading_point": {
        "set_torque": 3000,
        "-10mm": [2997, 2997, 2997, 2999, 2999],
        "+10mm": [3002, 3002, 3002, 3001, 3001]
    }
}

def test_complete_calculation_workflow():
    """Test complete calculation workflow API"""
    print("🧪 Testing Complete Calculation Workflow API")
    print("-" * 50)
    
    url = f"{BASE_URL}/calculations/jobs/{TEST_JOB_ID}/execute-complete-workflow"
    
    payload = {
        "measurement_data": EXCEL_MEASUREMENT_DATA,
        "config_name": "hydraulic_torque_wrench_standard",
        "auto_deviation_enabled": True
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Complete Workflow API - SUCCESS")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Success: {result.get('success')}")
            print(f"   Deviations: {result.get('deviation_count')}")
            print(f"   Status: {result.get('calculation_status')}")
            print(f"   Execution Time: {result.get('execution_time')}")
            return True
        else:
            print(f"❌ Complete Workflow API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Complete Workflow API - ERROR: {e}")
        return False

def test_stage_calculations():
    """Test individual stage calculation APIs"""
    print("\n🔍 Testing Individual Stage Calculation APIs")
    print("-" * 50)
    
    # Test Stage 1
    url = f"{BASE_URL}/calculations/jobs/{TEST_JOB_ID}/calculate/stage1"
    payload = {"measurement_data": EXCEL_MEASUREMENT_DATA}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Stage 1 API - SUCCESS")
            result = response.json()
            print(f"   Stage: {result.get('stage')} - {result.get('stage_name')}")
            print(f"   Success: {result.get('success')}")
        else:
            print(f"❌ Stage 1 API - FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Stage 1 API - ERROR: {e}")

def test_formula_interpolation():
    """Test formula interpolation APIs"""
    print("\n🔍 Testing Formula Interpolation APIs")
    print("-" * 50)
    
    test_torque_values = [3000, 6000, 12000]
    
    for torque_value in test_torque_values:
        url = f"{BASE_URL}/formulas/interpolate/torque-error/{torque_value}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Interpolation for {torque_value} Nm - SUCCESS")
                print(f"   Interpolated Error: {result.get('interpolated_error')}")
                print(f"   Lookup Method: {result.get('lookup_method')}")
                print(f"   Confidence: {result.get('confidence')}")
            else:
                print(f"❌ Interpolation for {torque_value} Nm - FAILED: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Interpolation for {torque_value} Nm - ERROR: {e}")

def test_lookup_tables():
    """Test lookup table APIs"""
    print("\n📋 Testing Lookup Table APIs")
    print("-" * 50)
    
    # Get available lookup tables
    url = f"{BASE_URL}/formulas/lookup-tables/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            tables = response.json()
            print(f"✅ Lookup Tables API - SUCCESS")
            print(f"   Available Tables: {len(tables)}")
            
            for table in tables[:3]:  # Show first 3 tables
                print(f"   - {table.get('table_name')} ({table.get('lookup_type')})")
                
        else:
            print(f"❌ Lookup Tables API - FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lookup Tables API - ERROR: {e}")

def test_calculation_results():
    """Test calculation results retrieval"""
    print("\n📊 Testing Calculation Results APIs")
    print("-" * 50)
    
    # Get calculation results
    url = f"{BASE_URL}/calculations/jobs/{TEST_JOB_ID}/calculation-results"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()
            print("✅ Calculation Results API - SUCCESS")
            print(f"   Job ID: {results.get('job_id')}")
            print(f"   Total Calculations: {results.get('total_calculations')}")
            print(f"   Stages: {list(results.get('stages', {}).keys())}")
        else:
            print(f"❌ Calculation Results API - FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Calculation Results API - ERROR: {e}")

def test_calculation_summary():
    """Test calculation summary API"""
    print("\n📈 Testing Calculation Summary API")
    print("-" * 50)
    
    url = f"{BASE_URL}/calculations/jobs/{TEST_JOB_ID}/calculation-summary"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            summary = response.json()
            print("✅ Calculation Summary API - SUCCESS")
            print(f"   Job ID: {summary.get('job_id')}")
            print(f"   Status: {summary.get('calculation_status')}")
            print(f"   Stages Completed: {summary.get('stages_completed')}")
            print(f"   Success Rate: {summary.get('overall_success_rate'):.1f}%")
        else:
            print(f"❌ Calculation Summary API - FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Calculation Summary API - ERROR: {e}")

def test_engine_status():
    """Test calculation engine status"""
    print("\n🔧 Testing Calculation Engine Status API")
    print("-" * 50)
    
    url = f"{BASE_URL}/calculations/calculation-engine/status"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            status = response.json()
            print("✅ Engine Status API - SUCCESS")
            print(f"   Engine Status: {status.get('engine_status')}")
            print(f"   Version: {status.get('version')}")
            print(f"   Configurations: {status.get('active_configurations')}")
            print(f"   Lookup Tables: {status.get('available_lookup_tables')}")
        else:
            print(f"❌ Engine Status API - FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Engine Status API - ERROR: {e}")

def test_excel_compliance():
    """Test Excel compliance check"""
    print("\n✅ Testing Excel Compliance API")
    print("-" * 50)
    
    url = f"{BASE_URL}/formulas/excel-compliance"
    params = {"torque_values": [3000, 6000, 12000]}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            compliance = response.json()
            print("✅ Excel Compliance API - SUCCESS")
            print(f"   Overall Compliance: {compliance.get('overall_compliance'):.1f}%")
            print(f"   Formula Status: {compliance.get('excel_formula_status')}")
            
            for result in compliance.get('test_results', []):
                status = "✅" if result.get('excel_compliant') else "❌"
                print(f"   {status} {result.get('torque_value')} Nm: {result.get('notes')}")
                
        else:
            print(f"❌ Excel Compliance API - FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Excel Compliance API - ERROR: {e}")

def run_all_tests():
    """Run all Phase 2 API tests"""
    print("🚀 PHASE 2 API TESTING SUITE")
    print("=" * 70)
    print("Testing enhanced calculation engine APIs with Excel data")
    print()
    
    # Test all APIs
    tests = [
        test_complete_calculation_workflow,
        test_stage_calculations,
        test_formula_interpolation,
        test_lookup_tables,
        test_calculation_results,
        test_calculation_summary,
        test_engine_status,
        test_excel_compliance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 PHASE 2 API TEST SUMMARY")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Phase 2 APIs are ready!")
    else:
        print("⚠️ Some tests failed - Review API implementations")
    
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()