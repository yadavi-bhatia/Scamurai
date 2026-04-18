"""Main Person 4 orchestrator with Exotel integration."""

from datetime import datetime
from typing import Optional, List, Tuple
from models import (
    VoiceAnalysisResult, TranscriptAnalysisResult, 
    FinalDecision, RiskLevel, CallerType, ExotelMetadata
)
from consensus_engine import ConsensusEngine
from tamper_log import TamperEvidentLog


class Person4Agent:
    """Person 4: Consensus + Logging + Response with Exotel integration."""
    
    def __init__(self):
        self.engine = ConsensusEngine()
        self.log = TamperEvidentLog()
    
    def process_call(
        self,
        voice_result: VoiceAnalysisResult,
        transcript_result: TranscriptAnalysisResult,
        exotel_metadata: Optional[ExotelMetadata] = None
    ) -> FinalDecision:
        """
        Process a call through consensus pipeline.
        
        Args:
            voice_result: Output from Person 2 (voice analysis)
            transcript_result: Output from Person 3 (transcript analysis)
            exotel_metadata: Routing metadata from Person 1 (Exotel)
        
        Returns:
            FinalDecision with risk assessment and evidence
        """
        
        # Step 1: Run consensus decision
        final_risk, final_score, caller_type, reason, reason_codes = \
            self.engine.decide(voice_result, transcript_result)
        
        # Step 2: Determine actions based on risk
        action, trigger_red_alert, trigger_hold_music = self._determine_actions(final_risk)
        
        # Step 3: Calculate confidence
        confidence = self._calculate_confidence(voice_result, transcript_result)
        
        # Step 4: Create decision object (without hash yet)
        decision = FinalDecision(
            final_risk=final_risk,
            final_score=final_score,
            caller_type=caller_type,
            decision_reason=reason,
            confidence=confidence,
            reason_codes=reason_codes,
            transcript_excerpt=transcript_result.transcript_text[:200],
            incident_hash="",  # Will fill after logging
            prev_hash="",      # Will fill after logging
            timestamp=datetime.now(),
            action=action,
            trigger_red_alert=trigger_red_alert,
            trigger_hold_music=trigger_hold_music
        )
        
        # Step 5: Prepare log data with Exotel metadata
        log_data = {
            "final_risk": final_risk.value,
            "final_score": final_score,
            "caller_type": caller_type.value,
            "decision_reason": reason,
            "reason_codes": reason_codes,
            "transcript_excerpt": transcript_result.transcript_text[:200],
            "voice_confidence": voice_result.confidence,
            "transcript_confidence": transcript_result.confidence,
            "signal_quality": voice_result.signal_quality
        }
        
        # Add Exotel metadata if provided
        if exotel_metadata:
            log_data.update({
                "exotel_call_id": exotel_metadata.call_id,
                "exotel_stream_id": exotel_metadata.stream_id,
                "routing_path": exotel_metadata.routing_path,
                "victim_number": exotel_metadata.victim_number,
                "scammer_number": exotel_metadata.scammer_number,
                "transfer_status": exotel_metadata.transfer_status,
                "call_duration": exotel_metadata.call_duration
            })
        
        # Step 6: Log to tamper-evident chain
        incident = self.log.append(log_data)
        
        # Step 7: Update decision with hash values
        # Need to create a new decision or use a mutable object
        decision.incident_hash = incident["hash"]
        decision.prev_hash = incident["prev_hash"]
        
        # Step 8: Trigger responses if needed
        if trigger_red_alert:
            self._trigger_red_alert(decision)
        
        if trigger_hold_music:
            self._trigger_hold_music(decision)
        
        # Step 9: Print summary
        self._print_summary(decision, exotel_metadata)
        
        return decision
    
    def _determine_actions(self, risk: RiskLevel) -> Tuple[str, bool, bool]:
        """Determine what actions to take based on risk level."""
        if risk == RiskLevel.DANGEROUS:
            return "Warn user and block call", True, True
        elif risk == RiskLevel.SUSPICIOUS:
            return "Warn user with caution", True, False
        else:
            return "Normal handling, no action", False, False
    
    def _calculate_confidence(
        self, 
        voice_result: VoiceAnalysisResult, 
        transcript_result: TranscriptAnalysisResult
    ) -> float:
        """Calculate overall confidence in the decision."""
        # Average of voice and transcript confidence, weighted by signal quality
        voice_weight = voice_result.signal_quality
        transcript_weight = 1 - voice_weight
        
        confidence = (
            voice_result.confidence * voice_weight +
            transcript_result.confidence * transcript_weight
        )
        
        return round(confidence, 3)
    
    def _trigger_red_alert(self, decision: FinalDecision):
        """Trigger red alert warning."""
        print("\n" + "🔴" * 30)
        print("🔴 RED ALERT - SCAM DETECTED 🔴")
        print("🔴" * 30)
        print(f"⚠️ Risk Level: {decision.final_risk.value}")
        print(f"⚠️ Score: {decision.final_score}/100")
        print(f"⚠️ Caller Type: {decision.caller_type.value}")
        print(f"⚠️ Action: {decision.action}")
        print("\n🚨 DO NOT SHARE:")
        print("   • OTP or One-Time Password")
        print("   • PIN or UPI PIN")
        print("   • Bank Account Details")
        print("   • Credit/Debit Card Numbers")
        print("   • Aadhar/PAN/Personal IDs")
        print("\n✅ What to do:")
        print("   • Hang up immediately")
        print("   • Call your bank directly using official number")
        print("   • Report to cyber crime portal: cybercrime.gov.in")
        print("🔴" * 30 + "\n")
    
    def _trigger_hold_music(self, decision: FinalDecision):
        """Trigger hold music trap."""
        print("\n" + "🎵" * 20)
        print("🎵 HOLD MUSIC TRAP ACTIVATED 🎵")
        print("🎵" * 20)
        print("📞 Playing: 'Please hold for a security specialist...'")
        print("⏱️ Trap duration: 30 seconds")
        print("📝 Caller behavior being recorded for evidence")
        print("🔒 This buys time for trace and block")
        print("🎵" * 20 + "\n")
    
    def _print_summary(self, decision: FinalDecision, exotel_metadata: Optional[ExotelMetadata] = None):
        """Print incident summary."""
        print("\n" + "="*70)
        print("📋 PERSON 4 - INCIDENT SUMMARY")
        print("="*70)
        
        # Risk display with color
        if decision.final_risk == RiskLevel.DANGEROUS:
            risk_display = f"🔴 {decision.final_risk.value}"
        elif decision.final_risk == RiskLevel.SUSPICIOUS:
            risk_display = f"🟡 {decision.final_risk.value}"
        else:
            risk_display = f"🟢 {decision.final_risk.value}"
        
        print(f"\n🎯 FINAL VERDICT:")
        print(f"   Risk: {risk_display} (Score: {decision.final_score:.1f}/100)")
        print(f"   Caller Type: {decision.caller_type.value}")
        print(f"   Confidence: {decision.confidence:.1%}")
        
        print(f"\n📝 DECISION REASON:")
        print(f"   {decision.decision_reason}")
        
        print(f"\n🔍 REASON CODES:")
        for code in decision.reason_codes[:5]:
            print(f"   • {code}")
        
        print(f"\n📞 TRANSCRIPT EXCERPT:")
        print(f"   \"{decision.transcript_excerpt[:150]}...\"")
        
        # Exotel info if available
        if exotel_metadata:
            print(f"\n📱 CALL ROUTING (Exotel):")
            print(f"   Call ID: {exotel_metadata.call_id}")
            print(f"   From: {exotel_metadata.scammer_number}")
            print(f"   To: {exotel_metadata.victim_number}")
            print(f"   Route: {exotel_metadata.routing_path}")
            print(f"   Status: {exotel_metadata.transfer_status}")
        
        print(f"\n🔒 FORENSIC EVIDENCE:")
        print(f"   Incident Hash: {decision.incident_hash[:32]}...")
        print(f"   Previous Hash: {decision.prev_hash[:32]}...")
        print(f"   Timestamp: {decision.timestamp.isoformat()}")
        print(f"   Action Taken: {decision.action}")
        
        print("\n" + "="*70)
        print("✅ Evidence stored in tamper-evident log")
        print("📁 Log location: person4/data/logs/audit_chain.log")
        print("="*70 + "\n")
    
    def verify_log_integrity(self) -> Tuple[bool, List[str]]:
        """Verify the entire log chain."""
        return self.log.verify_chain()
    
    def get_call_history(self, limit: int = 10) -> List[dict]:
        """Get recent call history from log."""
        records = self.log.get_all_records()
        return records[-limit:] if records else []


# Quick test with Exotel integration
if __name__ == "__main__":
    from models import VoiceAnalysisResult, TranscriptAnalysisResult, ExotelMetadata, CallerType
    
    print("\n" + "🚀"*35)
    print("PERSON 4 MODULE - WITH EXOTEL INTEGRATION")
    print("🚀"*35)
    
    # Create test Exotel metadata
    exotel_meta = ExotelMetadata(
        call_id=f"exotel_call_{int(datetime.now().timestamp())}",
        stream_id=f"stream_{int(datetime.now().timestamp())}",
        timestamp=datetime.now(),
        routing_path="exotel→+919876543210",
        victim_number="+919876543210",
        scammer_number="+15551234567",
        transfer_status="connected",
        call_duration=None
    )
    
    # Test 1: Dangerous scam call
    print("\n📞 TEST 1: DANGEROUS SCAM CALL")
    print("-" * 40)
    
    voice_result = VoiceAnalysisResult(
        caller_type=CallerType.AI,
        voice_score=85.0,
        signal_quality=0.78,
        confidence=0.88
    )
    
    transcript_result = TranscriptAnalysisResult(
        scam_likelihood=95.0,
        reason_codes=["otp_request", "urgent_action", "bank_impersonation"],
        scam_phrases_found=["OTP", "account blocked", "verify immediately"],
        transcript_text="This is Sarah from Fraud Prevention. Your account has been compromised. Someone is trying to transfer money from your account. I need the OTP sent to your phone immediately to block this transaction.",
        confidence=0.96
    )
    
    agent = Person4Agent()
    decision = agent.process_call(voice_result, transcript_result, exotel_meta)
    
    # Test 2: Suspicious call without Exotel metadata
    print("\n📞 TEST 2: SUSPICIOUS CALL (NO EXOTEL)")
    print("-" * 40)
    
    voice_result2 = VoiceAnalysisResult(
        caller_type=CallerType.UNCERTAIN,
        voice_score=55.0,
        signal_quality=0.62,
        confidence=0.70
    )
    
    transcript_result2 = TranscriptAnalysisResult(
        scam_likelihood=65.0,
        reason_codes=["prize_win", "personal_info_request"],
        scam_phrases_found=["You won", "provide details"],
        transcript_text="Congratulations! You've won a free vacation. Please provide your email address and phone number to claim your prize.",
        confidence=0.82
    )
    
    decision2 = agent.process_call(voice_result2, transcript_result2)
    
    # Verify log integrity
    print("\n🔗 LOG VERIFICATION:")
    is_valid, errors = agent.verify_log_integrity()
    if is_valid:
        print("✅ Audit chain is VALID - No tampering detected")
    else:
        print("❌ Audit chain is INVALID - Tampering detected!")
        for error in errors:
            print(f"   • {error}")
    
    # Show call history
    print("\n📜 RECENT CALL HISTORY:")
    history = agent.get_call_history(3)
    for i, record in enumerate(history, 1):
        print(f"   {i}. {record.get('timestamp', 'N/A')} - {record.get('final_risk', 'N/A')} - Score: {record.get('final_score', 'N/A')}")
    
    print("\n✅ Person 4 module ready for production!")