
"""Hour 33: Final Trusted Contact Test - Verify alerts can be sent to trusted contacts."""

import requests
import json
from datetime import datetime

def test_trusted_contacts():
    print("\n" + "="*60)
    print("🔍 HOUR 33: FINAL TRUSTED CONTACT TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Add trusted contact
    print("\n📋 Test 1: Add a trusted contact")
    try:
        response = requests.post(
            "http://127.0.0.1:8010/trusted/contacts",
            json={
                "user_id": "demo_user",
                "name": "Emergency Contact",
                "phone_number": "+919876543210",
                "relationship": "family"
            },
            timeout=5
        )
        result = response.json()
        print(f"   Response: {result.get('message', '')}")
        results.append(("Add trusted contact", result.get("success", False)))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Add trusted contact", False))
    
    # Test 2: Get contacts list
    print("\n📋 Test 2: Retrieve contacts list")
    try:
        response = requests.get(
            "http://127.0.0.1:8010/trusted/contacts/demo_user",
            timeout=5
        )
        result = response.json()
        print(f"   Total contacts: {result.get('total', 0)}")
        results.append(("Get contacts", result.get('total', 0) > 0))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Get contacts", False))
    
    # Test 3: Send alert to trusted contact
    print("\n📋 Test 3: Send scam alert to trusted contact")
    try:
        response = requests.post(
            "http://127.0.0.1:8010/trusted/share",
            json={
                "user_id": "demo_user",
                "contact_ids": ["c_0"],
                "caller_number": "+15551234567",
                "scam_category": "Bank Fraud",
                "reason": "OTP request detected with urgent language",
                "amount_at_risk": 50000
            },
            timeout=5
        )
        result = response.json()
        print(f"   Alert ID: {result.get('alert_id', 'N/A')}")
        print(f"   Contacts notified: {result.get('contacts_notified', 0)}")
        print(f"   Contact names: {result.get('contact_names', [])}")
        results.append(("Send alert", result.get("success", False)))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Send alert", False))
    
    # Test 4: Check alert history
    print("\n📋 Test 4: Verify alert history")
    try:
        response = requests.get(
            "http://127.0.0.1:8010/trusted/history/demo_user",
            timeout=5
        )
        result = response.json()
        print(f"   Total alerts: {result.get('total', 0)}")
        results.append(("Alert history", result.get('total', 0) > 0))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Alert history", False))
    
    # Test 5: Get trusted statistics
    print("\n📋 Test 5: Get trusted contacts statistics")
    try:
        response = requests.get(
            "http://127.0.0.1:8010/trusted/stats",
            timeout=5
        )
        result = response.json()
        print(f"   Total users: {result.get('total_users', 0)}")
        print(f"   Total contacts: {result.get('total_contacts', 0)}")
        print(f"   Total alerts sent: {result.get('total_alerts_sent', 0)}")
        results.append(("Get stats", result.get("success", False)))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Get stats", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL TRUSTED CONTACT TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for test, passed_flag in results:
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"   {status} - {test}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TRUSTED CONTACT TEST COMPLETE - ALL WORKING!")
    else:
        print("\n⚠️ Some tests failed. Please check server status.")
    
    return passed == total

if __name__ == "__main__":
    test_trusted_contacts()
