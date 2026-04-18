"""Complete final test for Person 4 system."""

import sys
import json
import requests
import subprocess
import time
import signal
import os

def print_section(title):
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def test_imports():
    print_section("Testing Imports")
    try:
        from models import VoiceAnalysisResult, TranscriptAnalysisResult, ExotelMetadata, FinalDecision, RiskLevel, CallerType
        print("✅ models.py - OK")
        from consensus_engine import ConsensusEngine
        print("✅ consensus_engine.py - OK")
        from tamper_log import TamperEvidentLog
        print("✅ tamper_log.py - OK")
        from main import Person4Agent
        print("✅ main.py - OK")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_consensus():
    print_section("Testing Consensus Engine")
    try:
        from models import VoiceAnalysisResult, TranscriptAnalysisResult, CallerType, RiskLevel
        from consensus_engine import ConsensusEngine
        
        engine = ConsensusEngine()
        
        # Test 1: Scam call
        voice = VoiceAnalysisResult(caller_type=CallerType.AI, voice_score=85, signal_quality=0.8, confidence=0.9)
        transcript = TranscriptAnalysisResult(scam_likelihood=95, reason_codes=['otp'], scam_phrases_found=['OTP'], transcript_text='Share OTP', confidence=0.95)
        risk, score, caller, reason, codes = engine.decide(voice, transcript)
        assert risk == RiskLevel.DANGEROUS
        print(f"✅ Scam detected: {risk.value} ({score:.0f}%)")
        
        # Test 2: Safe call
        voice2 = VoiceAnalysisResult(caller_type=CallerType.HUMAN, voice_score=10, signal_quality=0.9, confidence=0.95)
        transcript2 = TranscriptAnalysisResult(scam_likelihood=5, reason_codes=[], scam_phrases_found=[], transcript_text='Hello', confidence=0.98)
        risk2, score2, caller2, reason2, codes2 = engine.decide(voice2, transcript2)
        assert risk2 == RiskLevel.SAFE
        print(f"✅ Safe call detected: {risk2.value} ({score2:.0f}%)")
        
        return True
    except Exception as e:
        print(f"❌ Consensus test failed: {e}")
        return False

def test_logging():
    print_section("Testing Tamper-Evident Log")
    try:
        from tamper_log import TamperEvidentLog
        
        log = TamperEvidentLog()
        is_valid, errors = log.verify_chain()
        records = log.get_all_records()
        
        print(f"✅ Log valid: {is_valid}")
        print(f"✅ Total records: {len(records)}")
        if records:
            print(f"✅ Last record hash: {records[-1].get('hash', '')[:16]}...")
        return True
    except Exception as e:
        print(f"❌ Log test failed: {e}")
        return False

def test_server():
    print_section("Testing FastAPI Server")
    try:
        import subprocess
        import time
        import requests
        
        # Start server
        server_process = subprocess.Popen(
            ["python", "full_server.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8001/health")
        assert response.status_code == 200
        print("✅ Health endpoint - OK")
        
        # Test root endpoint
        response = requests.get("http://127.0.0.1:8001/")
        assert response.status_code == 200
        print("✅ Root endpoint - OK")
        
        # Test webhook
        payload = {
            "CallSid": "FINAL_TEST",
            "To": "+919876543210",
            "From": "+15551234567"
        }
        response = requests.post("http://127.0.0.1:8001/exotel-webhook", json=payload)
        assert response.status_code == 200
        result = response.json()
        print(f"✅ Webhook response: {result.get('data', {}).get('action', 'unknown')}")
        
        # Stop server
        server_process.terminate()
        time.sleep(1)
        
        return True
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    print("\n" + "🎯"*35)
    print("PERSON 4 - FINAL SYSTEM VERIFICATION")
    print("🎯"*35)
    
    tests = [
        ("Import Tests", test_imports),
        ("Consensus Engine", test_consensus),
        ("Tamper-Evident Log", test_logging),
        ("FastAPI Server", test_server)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print_section("FINAL RESULTS")
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 CONGRATULATIONS! All tests PASSED!")
        print("✅ Your Person 4 system is FULLY FUNCTIONAL!")
        print("\n📋 System Summary:")
        print("   • Consensus Engine: Working")
        print("   • Tamper-Evident Log: Active")
        print("   • FastAPI Server: Running")
        print("   • Exotel Webhook: Ready")
        print("\n🚀 Ready for Demo!")
    else:
        print("⚠️ Some tests FAILED. Please check the errors above.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
