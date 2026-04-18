
"""Hour 32: Final Blocklist Test - Verify numbers are blocked and reported correctly."""

import requests
import json
from datetime import datetime

def test_blocklist():
    print("\n" + "="*60)
    print("🔍 HOUR 32: FINAL BLOCKLIST & REPORT TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Block a new number
    print("\n📋 Test 1: Block a new number")
    try:
        response = requests.post(
            "http://127.0.0.1:8008/blocklist/block",
            json={
                "phone_number": "+15559998888",
                "reason": "Test scam detection",
                "verdict": "DANGEROUS",
                "risk_score": 95,
                "user_id": "test_user"
            },
            timeout=5
        )
        result = response.json()
        print(f"   Response: {result}")
        results.append(("Block new number", result.get("success", False)))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Block new number", False))
    
    # Test 2: Check if blocked
    print("\n📋 Test 2: Verify number is blocked")
    try:
        response = requests.get(
            "http://127.0.0.1:8008/blocklist/check/+15559998888?user_id=test_user",
            timeout=5
        )
        result = response.json()
        print(f"   Response: {result}")
        results.append(("Verify blocked", result.get("is_blocked", False)))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Verify blocked", False))
    
    # Test 3: Report to reputation list
    print("\n📋 Test 3: Report number to reputation list")
    try:
        response = requests.post(
            "http://127.0.0.1:8009/reputation/report",
            json={
                "phone_number": "+15559998888",
                "verdict": "DANGEROUS",
                "tags": ["test_scam", "otp_request"],
                "confidence": 0.95,
                "source": "test",
                "user_id": "test_user"
            },
            timeout=5
        )
        result = response.json()
        print(f"   Response: {result}")
        results.append(("Report to reputation", result.get("success", False)))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Report to reputation", False))
    
    # Test 4: Check reputation score
    print("\n📋 Test 4: Verify reputation score increased")
    try:
        response = requests.get(
            "http://127.0.0.1:8009/reputation/+15559998888",
            timeout=5
        )
        result = response.json()
        print(f"   Reputation Score: {result.get('reputation_score', 0)}")
        print(f"   Total Reports: {result.get('total_reports', 0)}")
        print(f"   Risk Level: {result.get('risk_level', 'unknown')}")
        results.append(("Reputation updated", result.get('reputation_score', 0) > 0))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(("Reputation updated", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL BLOCKLIST TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for test, passed_flag in results:
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"   {status} - {test}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 BLOCKLIST TEST COMPLETE - ALL WORKING!")
    else:
        print("\n⚠️ Some tests failed. Please check server status.")
    
    return passed == total

if __name__ == "__main__":
    test_blocklist()
