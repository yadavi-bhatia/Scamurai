"""
Test suite for Linguistic Agent
Tests various scenarios to verify detection accuracy
"""

import json
from linguistic_agent import LinguisticAgent


def run_test_suite():
    """Run complete test suite"""
    
    print("=" * 70)
    print("LINGUISTIC AGENT TEST SUITE")
    print("=" * 70)
    
    agent = LinguisticAgent(use_mock_asr=True)
    
    # Test Case 1: Scam Call (High Risk)
    print("\n📞 TEST 1: SCAM CALL (Expected: High Risk)")
    print("-" * 50)
    scam_transcript = """
    Hello? This is Jessica from Visa fraud department. Someone just tried to purchase $500 in gift cards.
    Do not hang up. This is urgent. I need you to go to the store and buy Bitcoin immediately.
    Do not tell anyone what you're doing. Your social security number has been compromised.
    If you don't do this right now, we will issue an arrest warrant.
    """
    result1 = agent.analyze_text_transcript(scam_transcript)
    print_result(result1)
    
    # Test Case 2: Normal Human Call (Low Risk)
    print("\n📞 TEST 2: NORMAL HUMAN CALL (Expected: Low Risk)")
    print("-" * 50)
    human_transcript = """
    Hi, um, I'm calling about my account. I think there's a charge I don't recognize.
    Let me see... it was for like $49.99. Actually, could you help me understand what that is?
    Thank you so much for your help. I really appreciate it.
    """
    result2 = agent.analyze_text_transcript(human_transcript)
    print_result(result2)
    
    # Test Case 3: Mixed / Uncertain Call
    print("\n📞 TEST 3: MIXED CALL (Expected: Medium/Uncertain Risk)")
    print("-" * 50)
    mixed_transcript = """
    Hello? I received a call about my account being compromised.
    I need to verify some information. Please don't hang up, I'm trying to help you.
    Um, actually I'm not sure about this. Let me talk to my wife first.
    """
    result3 = agent.analyze_text_transcript(mixed_transcript)
    print_result(result3)
    
    # Test Case 4: Short Call
    print("\n📞 TEST 4: SHORT CALL (Expected: Low/Medium Risk)")
    print("-" * 50)
    short_transcript = "Hello? Is someone there? I think I got a wrong number."
    result4 = agent.analyze_text_transcript(short_transcript)
    print_result(result4)
    
    # Test Case 5: High Urgency Scam
    print("\n📞 TEST 5: HIGH URGENCY SCAM (Expected: Very High Risk)")
    print("-" * 50)
    urgent_scam = """
    Your account will be CLOSED immediately! Don't hang up! Send $1000 in Bitcoin right now!
    This is your final warning. The police are on their way.
    """
    result5 = agent.analyze_text_transcript(urgent_scam)
    print_result(result5)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ All tests completed")
    print(f"📊 Risk score range: {min([r['linguistic_risk_score'] for r in [result1, result2, result3, result4, result5]])} - {max([r['linguistic_risk_score'] for r in [result1, result2, result3, result4, result5]])}")
    print(f"🎯 Scam detection threshold suggested: 0.65")
    print(f"👤 Human detection threshold suggested: 0.35")
    print(f"❓ Uncertain range: 0.35 - 0.65")


def print_result(result):
    """Pretty print test result"""
    print(f"  Risk Score: {result['linguistic_risk_score']} ", end="")
    if result['linguistic_risk_score'] > 0.7:
        print("🔴 HIGH RISK")
    elif result['linguistic_risk_score'] < 0.3:
        print("🟢 LOW RISK")
    else:
        print("🟡 UNCERTAIN")
    
    print(f"  Caller Type: {result['caller_type_hint']}")
    print(f"  Scam Phrases Found: {result['scam_phrase_count']}")
    if result['unique_scam_phrases']:
        print(f"    → {', '.join(result['unique_scam_phrases'][:3])}")
    print(f"  Urgency Level: {result['urgency_level']}")
    print(f"  Contradictions: {result['contradictions_detected']}")
    print(f"  Human Indicators: {result['human_speech_indicators'] or 'none'}")
    print(f"  Notes: {result['notes']}")


def test_with_audio_files():
    """Test with actual audio files if they exist"""
    import os
    
    print("\n" + "=" * 70)
    print("AUDIO FILE TEST (if files exist)")
    print("=" * 70)
    
    agent = LinguisticAgent(use_mock_asr=False)
    
    test_files = [
        "test_audio/scam_call.wav",
        "test_audio/human_call.wav",
        "test_audio/noisy_call.wav"
    ]
    
    for audio_file in test_files:
        if os.path.exists(audio_file):
            print(f"\n📁 Testing: {audio_file}")
            print("-" * 40)
            result = agent.analyze_call(audio_file)
            print_result(result)
        else:
            print(f"\n⚠️ File not found: {audio_file}")


if __name__ == "__main__":
    run_test_suite()
    
    # Uncomment to test with actual audio files:
    # test_with_audio_files()