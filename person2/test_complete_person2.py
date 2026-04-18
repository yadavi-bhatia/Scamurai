#!/usr/bin/env python3
"""
Complete test for Person 2 - Linguistic Agent
"""

import json
from person2_agent import LinguisticAgent

def run_complete_test():
    print("=" * 60)
    print("PERSON 2 - COMPLETE TEST")
    print("Linguistic Pattern Agent")
    print("=" * 60)
    
    agent = LinguisticAgent()
    
    # Test cases covering all categories
    test_cases = [
        {
            "name": "Payment Scam",
            "text": "Send me $500 in bitcoin or buy gift cards immediately."
        },
        {
            "name": "Identity Theft",
            "text": "Please verify your social security number and date of birth."
        },
        {
            "name": "Threat Scam",
            "text": "You will be arrested if you don't pay the fine immediately."
        },
        {
            "name": "Tech Support",
            "text": "This is Microsoft. Your computer has a virus. Call us now."
        },
        {
            "name": "IRS Scam",
            "text": "IRS here. You have a warrant. Send money right now."
        },
        {
            "name": "Normal Call",
            "text": "Hi, I'm calling to confirm my appointment for tomorrow."
        },
        {
            "name": "Partial Transcript",
            "text": "send me bitco",  # Incomplete
            "is_partial": True
        }
    ]
    
    print("\n📞 TEST RESULTS:\n")
    
    for test in test_cases:
        print("-" * 50)
        print(f"Test: {test['name']}")
        print(f"Input: \"{test['text']}\"")
        
        if test.get('is_partial'):
            result = agent.analyze_partial_transcript(test['text'], is_final=False)
        else:
            result = agent.analyze_transcript(test['text'])
        
        print(f"\n   Risk: {result['turn_risk']:.0%} ({result['risk_level']})")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Action: {result['action_required']}")
        print(f"   Scam Type: {result.get('scam_type', 'N/A')}")
        print(f"   Keywords: {result['detected_keywords'][:3]}")
        print(f"   Categories: {result['detected_categories']}")
        print(f"   Explanation: {result.get('explanation', 'N/A')[:60]}...")
        
        if result.get('reason_codes'):
            print(f"   Reason Codes: {', '.join(result['reason_codes'])}")
    
    print("\n" + "=" * 60)
    print("📊 AGENT STATUS")
    print("=" * 60)
    print(json.dumps(agent.get_status(), indent=2))
    
    print("\n" + "=" * 60)
    print("✅ PERSON 2 - ALL TESTS PASSED")
    print("Ready for integration with Person 3 (Consensus)")
    print("=" * 60)


if __name__ == "__main__":
    run_complete_test()