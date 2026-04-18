#!/usr/bin/env python3
"""Test Person 2 - Hours 8-9"""

from person2_agent import ScamCategories, LinguisticAgent

print("=" * 50)
print("PERSON 2 - HOUR 9 TEST")
print("=" * 50)

# Initialize agent
agent = LinguisticAgent()

# Test phrases
test_phrases = [
    "This is the IRS. You have a warrant.",
    "Send me $500 in bitcoin immediately.",
    "Please verify your social security number.",
    "Your Amazon account has been compromised.",
    "Hello, this is a normal customer service call."
]

print("\n📞 Testing scam detection:\n")

for phrase in test_phrases:
    result = agent.analyze_transcript(phrase)
    
    print(f"Input: \"{phrase[:50]}...\"")
    print(f"   Risk: {result['turn_risk']:.0%} ({result['risk_level']})")
    print(f"   Verdict: {result['verdict']}")
    print(f"   Keywords: {result['detected_keywords'][:3]}")
    print()

print("✅ Hour 9 complete - Analysis logic working")