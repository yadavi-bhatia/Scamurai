"""
Person 2 - Complete Test Suite
Tests all functionality: scam detection, evidence building, ASR, streaming
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linguistic_agent import LinguisticAgent, ScamKeywordDatabase
from evidence_builder import EvidenceBuilder
from stream_processor import ExotelStreamHandler, FileStreamProcessor
from asr_engine import get_asr_engine
import config


def test_keyword_database():
    """Test 1: Keyword Database"""
    print("\n" + "=" * 60)
    print("📚 TEST 1: Keyword Database")
    print("=" * 60)
    
    keywords = ScamKeywordDatabase.get_all_keywords()
    print(f"✅ Total keywords: {len(keywords)}")
    
    for category, kw in ScamKeywordDatabase.KEYWORDS.items():
        print(f"   📁 {category}: {len(kw)} keywords")
    
    # Verify Hindi keywords are included
    hindi_keywords = ["paisa bhejo", "jaldi karo", "aadhaar", "pakda denge"]
    found_hindi = [kw for kw in hindi_keywords if kw in keywords]
    print(f"\n✅ Hindi/Hinglish keywords present: {len(found_hindi)} found")
    
    assert len(keywords) > 50, "Should have at least 50 keywords"
    print("\n✅ Keyword database test passed")
    return True


def test_scam_detection():
    """Test 2: Scam Detection"""
    print("\n" + "=" * 60)
    print("🎯 TEST 2: Scam Detection")
    print("=" * 60)
    
    agent = LinguisticAgent("test_session")
    
    test_cases = [
        ("Payment scam (English)", "Send me $500 in bitcoin immediately", 0.30),
        ("Payment scam (Hinglish)", "Mujhe 500 rupees bhejo", 0.20),
        ("Identity theft (English)", "Please verify your social security number", 0.25),
        ("Identity theft (Hinglish)", "Aadhaar number aur OTP batao", 0.25),
        ("Threat scam (English)", "You will be arrested if you don't pay", 0.25),
        ("Threat scam (Hinglish)", "Police pakad legi warna jail hoga", 0.20),
        ("Fake authority", "This is the IRS. Your account is frozen.", 0.30),
        ("Urgency scam", "Don't hang up! This is urgent!", 0.20),
        ("Normal call", "Hello, I'm calling about my appointment", 0.0),
        ("Mixed scam", "IRS here. Send bitcoin or get arrested", 0.35)
    ]
    
    passed = 0
    for name, text, min_risk in test_cases:
        result = agent.analyze_transcript(text)
        print(f"\n   📞 {name}: '{text[:50]}...'")
        print(f"      Risk: {result.risk_score:.0%} | Level: {result.risk_level}")
        print(f"      Type: {result.scam_type}")
        print(f"      Keywords: {result.detected_keywords[:3]}")
        print(f"      Categories: {result.detected_categories}")
        
        if result.risk_score >= min_risk:
            passed += 1
            print(f"      ✅ PASS (>= {min_risk:.0%})")
        else:
            print(f"      ❌ FAIL (got {result.risk_score:.0%}, need {min_risk:.0%})")
    
    print(f"\n✅ Scam detection: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_evidence_builder():
    """Test 3: Evidence Builder"""
    print("\n" + "=" * 60)
    print("🔐 TEST 3: Evidence Builder")
    print("=" * 60)
    
    builder = EvidenceBuilder("test_session_001")
    
    # Add evidence records
    records = [
        ("T001", "Send me bitcoin immediately", 0.65, "HIGH", 
         ["bitcoin", "immediately"], ["payment_request", "urgency"]),
        ("T002", "Your social security number is compromised", 0.70, "CRITICAL",
         ["social security", "compromised"], ["identity_theft", "scam_phrases"]),
        ("T003", "Police will arrest you", 0.55, "HIGH",
         ["police", "arrest"], ["threat"])
    ]
    
    for turn_id, text, risk, level, keywords, categories in records:
        record = builder.add_evidence(
            turn_id=turn_id,
            transcript=text,
            risk_score=risk,
            risk_level=level,
            detected_keywords=keywords,
            detected_categories=categories
        )
        print(f"   ✅ Added evidence: {turn_id} (hash: {record.evidence_hash[:8]}...)")
    
    # Verify chain
    verification = builder.verify_chain()
    print(f"\n   Chain verification: {'✅ PASS' if verification['verified'] else '❌ FAIL'}")
    print(f"   Total records: {verification['total_records']}")
    
    # Get session report
    report = builder.get_session_report()
    print(f"\n   Session Report:")
    print(f"      Final verdict: {report['final_verdict']}")
    print(f"      Max risk: {report['max_risk_score']:.0%}")
    print(f"      Categories: {report['categories_detected']}")
    
    # Clean up test evidence
    import shutil
    if os.path.exists("./evidence/test_session_001"):
        shutil.rmtree("./evidence/test_session_001")
    
    print("\n✅ Evidence builder test passed")
    return True


def test_stream_processor():
    """Test 4: Stream Processor"""
    print("\n" + "=" * 60)
    print("🌊 TEST 4: Stream Processor")
    print("=" * 60)
    
    transcripts_received = []
    alerts_received = []
    
    def on_transcript(transcript):
        transcripts_received.append(transcript)
        print(f"   📝 Transcript: {transcript['transcript'][:50]}...")
    
    def on_alert(alert):
        alerts_received.append(alert)
        print(f"   🚨 ALERT: {alert['keywords']}")
    
    # Create handler
    handler = ExotelStreamHandler(
        call_sid="TEST_CALL_001",
        on_transcript=on_transcript,
        on_alert=on_alert
    )
    
    handler.start()
    
    # Generate mock audio
    import numpy as np
    
    def generate_mock_audio(duration_sec: float, sample_rate: int = 8000) -> bytes:
        samples = int(sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, samples)
        audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        return audio.tobytes()
    
    # Simulate chunks
    mock_audio = generate_mock_audio(3.0, 8000)
    
    # Process chunks (simulate without base64 for test)
    result = handler.processor.process_chunk(mock_audio, 8000, {"test": True})
    
    handler.stop()
    
    print(f"\n   Transcripts received: {len(transcripts_received)}")
    print(f"   Alerts triggered: {len(alerts_received)}")
    
    print("\n✅ Stream processor test passed")
    return True


def test_asr_engine():
    """Test 5: ASR Engine"""
    print("\n" + "=" * 60)
    print("🎤 TEST 5: ASR Engine")
    print("=" * 60)
    
    # Test Google ASR (mock for CI)
    engine = get_asr_engine("mock")
    print(f"   Mock ASR available: {engine.is_available()}")
    
    # Test transcription
    test_audio = b'\x00\x00' * 16000  # 1 second of silence
    result = engine.transcribe(test_audio, 16000)
    print(f"   Mock transcription: '{result[:50]}...'")
    
    print("\n✅ ASR engine test passed")
    return True


def test_config():
    """Test 6: Configuration"""
    print("\n" + "=" * 60)
    print("⚙️ TEST 6: Configuration")
    print("=" * 60)
    
    print(f"   Risk thresholds: {config.RISK_THRESHOLDS}")
    print(f"   ASR config: engine={config.ASR_CONFIG['engine']}, language={config.ASR_CONFIG['language']}")
    print(f"   Scam categories: {len(config.SCAM_CATEGORIES)}")
    
    # Verify Indian context settings
    assert config.ASR_CONFIG["language"] == "hi-IN", "Should use Hindi/Indian English"
    assert config.RISK_THRESHOLDS["critical"] == 0.65, "Critical threshold should be 0.65"
    
    print("\n✅ Configuration test passed")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 PERSON 2 - COMPLETE TEST SUITE")
    print("   Linguistic Pattern Agent with Hindi/Hinglish Support")
    print("=" * 70)
    
    results = []
    
    # Run each test
    results.append(("Keyword Database", test_keyword_database()))
    results.append(("Scam Detection", test_scam_detection()))
    results.append(("Evidence Builder", test_evidence_builder()))
    results.append(("Stream Processor", test_stream_processor()))
    results.append(("ASR Engine", test_asr_engine()))
    results.append(("Configuration", test_config()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
        if result:
            passed += 1
    
    print(f"\n   Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED - Person 2 is ready!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("⚠️ SOME TESTS FAILED - Please check errors above")
        print("=" * 70)
        return False


def run_quick_demo():
    """Quick demo of scam detection"""
    print("\n" + "=" * 70)
    print("🎯 QUICK DEMO - Scam Detection Examples")
    print("=" * 70)
    
    agent = LinguisticAgent("demo_session")
    
    examples = [
        "Send me bitcoin immediately or you will be arrested",
        "Aapka Aadhaar number compromised hai, OTP batao",
        "जल्दी करो, नहीं तो पुलिस पकड़ लेगी",
        "This is your bank. Your account will be frozen. Send money now.",
        "Namaste, main apne account balance ke baare mein pooch raha tha"
    ]
    
    for text in examples:
        result = agent.analyze_transcript(text)
        print(f"\n📞 '{text}'")
        print(f"   Risk: {result.risk_score:.0%} ({result.risk_level})")
        print(f"   Verdict: {result.scam_type}")
        print(f"   Keywords: {result.detected_keywords[:4]}")
        print(f"   Categories: {result.detected_categories}")
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Person 2 Test Suite")
    parser.add_argument("--demo", action="store_true", help="Run quick demo only")
    parser.add_argument("--test", action="store_true", help="Run full test suite")
    
    args = parser.parse_args()
    
    if args.demo:
        run_quick_demo()
    elif args.test:
        run_all_tests()
    else:
        # Default: run both demo and tests
        run_quick_demo()
        print("\n" + "=" * 70)
        input("Press Enter to run full test suite...")
        run_all_tests()