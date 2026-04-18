
"""Simple final check for Person 4 system (no external dependencies)."""

import sys
import os
import json
from datetime import datetime

def print_section(title):
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def test_files():
    print_section("Checking File Structure")
    required_files = [
        "models.py",
        "consensus_engine.py", 
        "tamper_log.py",
        "main.py",
        "full_server.py",
        "data/logs/audit_chain.log"
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_exist = False
    
    return all_exist

def test_imports():
    print_section("Testing Imports")
    try:
        sys.path.insert(0, os.getcwd())
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
        voice = VoiceAnalysisResult(
            caller_type=CallerType.AI, 
            voice_score=85, 
            signal_quality=0.8, 
            confidence=0.9,
            raw_features=None
        )
        transcript = TranscriptAnalysisResult(
            scam_likelihood=95, 
            reason_codes=['otp_request'], 
            scam_phrases_found=['OTP'], 
            transcript_text='Share your OTP', 
            confidence=0.95
        )
        risk, score, caller, reason, codes = engine.decide(voice, transcript)
        
        if risk == RiskLevel.DANGEROUS:
            print(f"✅ Scam detected: {risk.value} ({score:.0f}%)")
        else:
            print(f"⚠️ Expected DANGEROUS, got {risk.value}")
            return False
        
        # Test 2: Safe call
        voice2 = VoiceAnalysisResult(
            caller_type=CallerType.HUMAN, 
            voice_score=10, 
            signal_quality=0.9, 
            confidence=0.95,
            raw_features=None
        )
        transcript2 = TranscriptAnalysisResult(
            scam_likelihood=5, 
            reason_codes=[], 
            scam_phrases_found=[], 
            transcript_text='Hello, how are you?', 
            confidence=0.98
        )
        risk2, score2, caller2, reason2, codes2 = engine.decide(voice2, transcript2)
        
        if risk2 == RiskLevel.SAFE:
            print(f"✅ Safe call detected: {risk2.value} ({score2:.0f}%)")
        else:
            print(f"⚠️ Expected SAFE, got {risk2.value}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Consensus test failed: {e}")
        import traceback
        traceback.print_exc()
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
            last = records[-1]
            print(f"✅ Last record hash: {last.get('hash', '')[:16]}...")
            print(f"✅ Last record risk: {last.get('final_risk', 'N/A')}")
        
        return is_valid
    except Exception as e:
        print(f"❌ Log test failed: {e}")
        return False

def test_main_agent():
    print_section("Testing Main Agent")
    try:
        from models import VoiceAnalysisResult, TranscriptAnalysisResult, CallerType, RiskLevel
        from main import Person4Agent
        
        agent = Person4Agent()
        
        voice = VoiceAnalysisResult(
            caller_type=CallerType.AI,
            voice_score=85,
            signal_quality=0.8,
            confidence=0.9,
            raw_features=None
        )
        
        transcript = TranscriptAnalysisResult(
            scam_likelihood=95,
            reason_codes=["otp_request"],
            scam_phrases_found=["OTP"],
            transcript_text="Share your OTP",
            confidence=0.95
        )
        
        decision = agent.process_call(voice, transcript)
        
        print(f"✅ Agent processed call")
        print(f"   Risk: {decision.final_risk.value}")
        print(f"   Score: {decision.final_score}")
        print(f"   Action: {decision.action}")
        print(f"   Hash: {decision.incident_hash[:16]}...")
        
        return True
    except Exception as e:
        print(f"❌ Main agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "🎯"*35)
    print("PERSON 4 - FINAL SYSTEM VERIFICATION")
    print("🎯"*35)
    
    tests = [
        ("File Structure", test_files),
        ("Imports", test_imports),
        ("Consensus Engine", test_consensus),
        ("Tamper-Evident Log", test_logging),
        ("Main Agent", test_main_agent)
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
        print("   • Main Agent: Ready")
        print("\n🚀 To start the server:")
        print("   python full_server.py")
        print("\n📝 To test the webhook:")
        print("   curl -X POST http://127.0.0.1:8001/exotel-webhook \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"CallSid\":\"test\",\"To\":\"+91\",\"From\":\"+1\"}'")
    else:
        print("⚠️ Some tests FAILED. Please check the errors above.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())