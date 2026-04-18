"""Complete demo showing Person 4 with Exotel integration."""

from datetime import datetime
from models import (
    VoiceAnalysisResult, TranscriptAnalysisResult, 
    ExotelMetadata, CallerType, RiskLevel
)
from main import Person4Agent

def run_complete_demo():
    print("\n" + "="*70)
    print("🎯 COMPLETE SCAM DETECTION DEMO - Person 4 with Exotel")
    print("="*70)
    
    # Simulate data from Person 1 (Exotel)
    exotel_data = ExotelMetadata(
        call_id=f"exotel_call_{int(datetime.now().timestamp())}",
        stream_id=f"stream_{int(datetime.now().timestamp())}",
        timestamp=datetime.now(),
        routing_path="exotel→+919876543210",
        victim_number="+919876543210",
        scammer_number="+1234567890",
        transfer_status="connected"
    )
    
    # Simulate data from Person 2 (Voice Agent)
    voice_data = VoiceAnalysisResult(
        caller_type=CallerType.AI,
        voice_score=85.0,
        signal_quality=0.75,
        confidence=0.88
    )
    
    # Simulate data from Person 3 (Transcript Agent)
    transcript_data = TranscriptAnalysisResult(
        scam_likelihood=92.0,
        reason_codes=["otp_request", "urgent_action", "bank_impersonation"],
        scam_phrases_found=["OTP", "account blocked", "verify now"],
        transcript_text="This is your bank. Your account has been compromised. Please verify your OTP code now to secure your account.",
        confidence=0.94
    )
    
    print("\n📞 INCOMING CALL FROM EXOTEL:")
    print(f"   Call ID: {exotel_data.call_id}")
    print(f"   From: {exotel_data.scammer_number}")
    print(f"   To: {exotel_data.victim_number}")
    
    print("\n🎙️ VOICE ANALYSIS (Person 2):")
    print(f"   Caller Type: {voice_data.caller_type.value}")
    print(f"   Voice Score: {voice_data.voice_score}/100")
    print(f"   Signal Quality: {voice_data.signal_quality}")
    
    print("\n📝 TRANSCRIPT ANALYSIS (Person 3):")
    print(f"   Scam Likelihood: {transcript_data.scam_likelihood}/100")
    print(f"   Reason Codes: {', '.join(transcript_data.reason_codes)}")
    
    # Process through Person 4
    agent = Person4Agent()
    decision = agent.process_call(voice_data, transcript_data, exotel_data)
    
    print("\n📊 FINAL VERDICT:")
    print(f"   Risk Level: {decision.final_risk.value}")
    print(f"   Score: {decision.final_score}/100")
    print(f"   Action: {decision.action}")
    
    # Show evidence packet
    print("\n🔒 EVIDENCE PACKET:")
    print(f"   Incident Hash: {decision.incident_hash[:32]}...")
    print(f"   Log File: data/logs/audit_chain.log")
    
    # Verify chain
    is_valid, errors = agent.log.verify_chain()
    print(f"\n🔗 Chain Verification: {'✓ VALID' if is_valid else '✗ TAMPERED'}")
    
    print("\n" + "="*70)
    print("✅ Demo Complete - System Ready for Production")
    print("="*70 + "\n")
    
    return decision

if __name__ == "__main__":
    run_complete_demo()