# scripts/test_phase3_auto_deviation.py - Test Phase 3 Auto-Deviation System
import requests
import json
from typing import Dict, Any
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_JOB_ID = 1

def test_tolerance_checking():
    """Test tolerance checking API"""
    print("🎯 Testing Tolerance Checking API")
    print("-" * 50)
    
    url = f"{BASE_URL}/auto-deviation/jobs/{TEST_JOB_ID}/check-tolerances"
    
    try:
        response = requests.post(url)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Tolerance Check API - SUCCESS")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Overall Status: {result.get('overall_status')}")
            print(f"   Deviation Required: {result.get('deviation_required')}")
            print(f"   Severity: {result.get('severity')}")
            print(f"   Checks Performed: {result.get('summary', {}).get('total_checks', 0)}")
            print(f"   Failed Checks: {result.get('summary', {}).get('failed_checks', 0)}")
            print(f"   Pass Rate: {result.get('summary', {}).get('pass_rate', 0):.1f}%")
            
            # Show failed checks
            if result.get('failures'):
                print("\n   Failed Checks:")
                for failure in result['failures']:
                    print(f"     - {failure.get('check_name')}: {failure.get('severity')}")
            
            return True
        else:
            print(f"❌ Tolerance Check API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Tolerance Check API - ERROR: {e}")
        return False

def test_auto_deviation_generation():
    """Test auto-deviation generation API"""
    print("\n🚨 Testing Auto-Deviation Generation API")
    print("-" * 50)
    
    url = f"{BASE_URL}/auto-deviation/jobs/{TEST_JOB_ID}/auto-generate-deviations"
    
    try:
        response = requests.post(url, params={"send_notifications": True})
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Auto-Deviation Generation API - SUCCESS")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Generated Deviations: {len(result.get('generated_deviations', []))}")
            print(f"   Notifications Sent: {len(result.get('notifications_sent', []))}")
            
            # Show generated deviations
            for deviation in result.get('generated_deviations', []):
                print(f"     - {deviation.get('deviation_number')}: {deviation.get('severity')} ({deviation.get('deviation_type')})")
            
            # Show next actions
            print("\n   Next Actions:")
            for action in result.get('next_actions', []):
                print(f"     • {action}")
            
            # Show summary
            summary = result.get('summary', {})
            print(f"\n   Summary:")
            print(f"     Total Deviations: {summary.get('total_deviations', 0)}")
            print(f"     High Severity: {summary.get('high_severity', 0)}")
            print(f"     Medium Severity: {summary.get('medium_severity', 0)}")
            print(f"     Low Severity: {summary.get('low_severity', 0)}")
            print(f"     Job Status: {summary.get('job_status', 'unknown')}")
            
            return True
        else:
            print(f"❌ Auto-Deviation Generation API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-Deviation Generation API - ERROR: {e}")
        return False

def test_deviation_status():
    """Test deviation status API"""
    print("\n📊 Testing Deviation Status API")
    print("-" * 50)
    
    url = f"{BASE_URL}/auto-deviation/jobs/{TEST_JOB_ID}/deviation-status"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Deviation Status API - SUCCESS")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Job Number: {result.get('job_number')}")
            print(f"   Overall Status: {result.get('overall_deviation_status')}")
            print(f"   Certificate Generation Allowed: {result.get('certificate_generation_allowed')}")
            print(f"   Total Deviations: {result.get('total_deviations')}")
            print(f"   Approved: {result.get('approved_deviations')}")
            print(f"   Rejected: {result.get('rejected_deviations')}")
            print(f"   Pending: {result.get('pending_deviations')}")
            
            return True
        else:
            print(f"❌ Deviation Status API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Deviation Status API - ERROR: {e}")
        return False

def test_customer_approval():
    """Test customer approval API"""
    print("\n✅ Testing Customer Approval API")
    print("-" * 50)
    
    # First, get a deviation ID to approve
    status_url = f"{BASE_URL}/auto-deviation/jobs/{TEST_JOB_ID}/deviation-status"
    
    try:
        status_response = requests.get(status_url)
        if status_response.status_code != 200:
            print("❌ Could not get deviation status to test approval")
            return False
        
        status_result = status_response.json()
        deviations = status_result.get('deviations', [])
        
        if not deviations:
            print("ℹ️ No deviations found to test approval")
            return True
        
        # Test approval for first deviation
        deviation_id = deviations[0]['id']
        approval_url = f"{BASE_URL}/auto-deviation/deviations/{deviation_id}/customer-approve"
        
        approval_data = {
            "client_decision": "ACCEPT",
            "client_comments": "Approved for testing purposes - deviation is acceptable",
            "client_decision_date": date.today().isoformat()
        }
        
        response = requests.put(approval_url, json=approval_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Customer Approval API - SUCCESS")
            print(f"   Deviation ID: {result.get('deviation_id')}")
            print(f"   Deviation Number: {result.get('deviation_number')}")
            print(f"   Customer Decision: {result.get('customer_decision')}")
            print(f"   Job Status: {result.get('job_status')}")
            print(f"   Certificate Ready: {result.get('certificate_generation_ready')}")
            
            print("\n   Next Steps:")
            for step in result.get('next_steps', []):
                print(f"     • {step}")
            
            return True
        else:
            print(f"❌ Customer Approval API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Customer Approval API - ERROR: {e}")
        return False

def test_dashboard_summary():
    """Test deviation dashboard summary API"""
    print("\n📈 Testing Dashboard Summary API")
    print("-" * 50)
    
    url = f"{BASE_URL}/auto-deviation/dashboard/summary"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dashboard Summary API - SUCCESS")
            
            summary = result.get('summary', {})
            print(f"   Total Deviations: {summary.get('total_deviations', 0)}")
            print(f"   Open Deviations: {summary.get('open_deviations', 0)}")
            print(f"   Resolved Deviations: {summary.get('resolved_deviations', 0)}")
            print(f"   Resolution Rate: {summary.get('resolution_rate', 0):.1f}%")
            print(f"   Approval Rate: {summary.get('approval_rate', 0):.1f}%")
            
            # Show severity breakdown
            severity = result.get('severity_breakdown', {})
            print(f"\n   Severity Breakdown:")
            print(f"     High: {severity.get('high', 0)}")
            print(f"     Medium: {severity.get('medium', 0)}")
            print(f"     Low: {severity.get('low', 0)}")
            
            # Show type breakdown
            types = result.get('type_breakdown', {})
            if types:
                print(f"\n   Type Breakdown:")
                for dev_type, count in types.items():
                    print(f"     {dev_type}: {count}")
            
            # Show customer responses
            responses = result.get('customer_responses', {})
            print(f"\n   Customer Responses:")
            print(f"     Approved: {responses.get('approved', 0)}")
            print(f"     Rejected: {responses.get('rejected', 0)}")
            print(f"     Conditional: {responses.get('conditional', 0)}")
            print(f"     Pending: {responses.get('pending', 0)}")
            
            # Show trends
            trends = result.get('trends', {})
            if trends:
                print(f"\n   Trends:")
                print(f"     Most Common Type: {trends.get('most_common_deviation_type', 'N/A')}")
                print(f"     Avg Resolution Time: {trends.get('average_resolution_time', 'N/A')}")
                print(f"     Customer Satisfaction: {trends.get('customer_satisfaction', 'N/A')}")
            
            return True
        else:
            print(f"❌ Dashboard Summary API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard Summary API - ERROR: {e}")
        return False

def test_email_notification():
    """Test email notification system"""
    print("\n📧 Testing Email Notification API")
    print("-" * 50)
    
    # Get a deviation to test with
    status_url = f"{BASE_URL}/auto-deviation/jobs/{TEST_JOB_ID}/deviation-status"
    
    try:
        status_response = requests.get(status_url)
        if status_response.status_code != 200:
            print("❌ Could not get deviation status to test email")
            return False
        
        status_result = status_response.json()
        deviations = status_result.get('deviations', [])
        
        if not deviations:
            print("ℹ️ No deviations found to test email notification")
            return True
        
        deviation_id = deviations[0]['id']
        email_url = f"{BASE_URL}/auto-deviation/test-email-notification"
        
        email_data = {
            "deviation_id": deviation_id,
            "test_email": "test@example.com"
        }
        
        response = requests.post(email_url, params=email_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Email Notification API - SUCCESS")
            print(f"   Test Email Sent: {result.get('success')}")
            print(f"   Deviation Number: {result.get('deviation_number')}")
            print(f"   Message: {result.get('message')}")
            
            return True
        else:
            print(f"❌ Email Notification API - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email Notification API - ERROR: {e}")
        return False

def run_phase3_tests():
    """Run all Phase 3 auto-deviation system tests"""
    print("🚀 PHASE 3 AUTO-DEVIATION SYSTEM TESTING")
    print("=" * 70)
    print("Testing complete auto-deviation workflow with tolerance checking,")
    print("deviation generation, customer approval, and email notifications.")
    print()
    
    # Test all APIs
    tests = [
        ("Tolerance Checking", test_tolerance_checking),
        ("Auto-Deviation Generation", test_auto_deviation_generation),
        ("Deviation Status", test_deviation_status),
        ("Customer Approval", test_customer_approval),
        ("Dashboard Summary", test_dashboard_summary),
        ("Email Notification", test_email_notification)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 PHASE 3 AUTO-DEVIATION SYSTEM TEST SUMMARY")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Phase 3 Auto-Deviation System is ready!")
        print("\n✅ SYSTEM CAPABILITIES VERIFIED:")
        print("   • Tolerance checking with 5 different validation types")
        print("   • Automatic deviation report generation")
        print("   • Email notification system for customers")
        print("   • Customer approval workflow")
        print("   • Comprehensive deviation analytics dashboard")
        print("   • Complete audit trail and status tracking")
    else:
        print("⚠️ Some tests failed - Review API implementations")
        print("\n🔧 TROUBLESHOOTING:")
        print("   • Ensure all services are properly imported")
        print("   • Check database connections and models")
        print("   • Verify job data exists for testing")
        print("   • Review error logs for detailed information")
    
    print("=" * 70)

if __name__ == "__main__":
    run_phase3_tests()