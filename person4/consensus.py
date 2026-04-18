"""Consensus engine combining voice and transcript signals for live call scam detection."""

from typing import Tuple, List
from models import (
    RiskLevel, CallerType, VoiceAnalysisResult,
    TranscriptAnalysisResult
)


class ConsensusEngine:
    """Combines voice and transcript signals into final decision for live calls."""
    
    def __init__(self):
        # Risk thresholds (0-100 scale)
        self.RISK_THRESHOLD_SUSPICIOUS = 40
        self.RISK_THRESHOLD_DANGEROUS = 70
        
        # Weights for combining signals
        self.WEIGHT_TRANSCRIPT_HIGH_QUALITY = 0.7
        self.WEIGHT_VOICE_HIGH_QUALITY = 0.3
        self.WEIGHT_TRANSCRIPT_LOW_QUALITY = 0.85
        self.WEIGHT_VOICE_LOW_QUALITY = 0.15
        
        # Quality threshold (0-1 scale)
        self.SIGNAL_QUALITY_GOOD_THRESHOLD = 0.7
        
        # Scam phrase keywords for boosting score
        self.HIGH_RISK_PHRASES = [
            "otp", "one time password", "verification code", 
            "account blocked", "account compromised", "fraud alert",
            "immediate action", "urgent", "bank details", 
            "password", "upi pin", "credit card number"
        ]
        
        self.MEDIUM_RISK_PHRASES = [
            "prize", "won", "lottery", "refund", "customer care",
            "tech support", "virus detected", "security alert"
        ]
        
        # Urgent language indicators
        self.URGENT_WORDS = [
            "immediately", "right now", "asap", "urgent", 
            "now", "fast", "quickly", "immediate"
        ]
    
    def decide(
        self,
        voice_result: VoiceAnalysisResult,
        transcript_result: TranscriptAnalysisResult
    ) -> Tuple[RiskLevel, float, CallerType, str, List[str]]:
        """
        Make final decision based on all signals.
        
        Returns:
            (final_risk, final_score, caller_type, reason, reason_codes)
        """
        
        # Step 1: Calculate weighted score based on signal quality
        final_score = self._calculate_weighted_score(voice_result, transcript_result)
        
        # Step 2: Apply phrase-based boosting
        final_score, phrase_matches = self._apply_phrase_boosting(
            final_score, transcript_result
        )
        
        # Step 3: Apply special reconciliation rules
        final_score, caller_type, reason_codes = self._apply_special_rules(
            final_score, voice_result, transcript_result
        )
        
        # Add phrase matches to reason codes
        reason_codes.extend(phrase_matches)
        
        # Step 4: Determine risk level
        final_risk = self._get_risk_level(final_score)
        
        # Step 5: Generate explanation
        reason = self._generate_reason(
            final_risk, final_score, caller_type, 
            voice_result, transcript_result, reason_codes
        )
        
        return final_risk, final_score, caller_type, reason, reason_codes
    
    def _calculate_weighted_score(
        self,
        voice_result: VoiceAnalysisResult,
        transcript_result: TranscriptAnalysisResult
    ) -> float:
        """Calculate weighted score based on signal quality."""
        
        # Determine weights based on audio quality
        if voice_result.signal_quality >= self.SIGNAL_QUALITY_GOOD_THRESHOLD:
            transcript_weight = self.WEIGHT_TRANSCRIPT_HIGH_QUALITY
            voice_weight = self.WEIGHT_VOICE_HIGH_QUALITY
        else:
            # Poor audio quality - trust transcript more
            transcript_weight = self.WEIGHT_TRANSCRIPT_LOW_QUALITY
            voice_weight = self.WEIGHT_VOICE_LOW_QUALITY
        
        # Calculate weighted score
        transcript_score = transcript_result.scam_likelihood
        voice_score = voice_result.voice_score
        
        final_score = (transcript_score * transcript_weight) + (voice_score * voice_weight)
        
        return final_score
    
    def _apply_phrase_boosting(
        self,
        final_score: float,
        transcript_result: TranscriptAnalysisResult
    ) -> Tuple[float, List[str]]:
        """Boost score based on scam phrases detected."""
        
        phrase_matches = []
        transcript_lower = transcript_result.transcript_text.lower()
        
        # Check for high-risk phrases
        for phrase in self.HIGH_RISK_PHRASES:
            if phrase in transcript_lower:
                phrase_matches.append(f"high_risk_phrase_{phrase.replace(' ', '_')[:20]}")
                final_score = min(final_score + 15, 100)
        
        # Check for medium-risk phrases (only if not already high)
        if not phrase_matches:
            for phrase in self.MEDIUM_RISK_PHRASES:
                if phrase in transcript_lower:
                    phrase_matches.append(f"medium_risk_phrase_{phrase.replace(' ', '_')[:20]}")
                    final_score = min(final_score + 8, 100)
        
        return final_score, phrase_matches
    
    def _apply_special_rules(
        self,
        final_score: float,
        voice_result: VoiceAnalysisResult,
        transcript_result: TranscriptAnalysisResult
    ) -> Tuple[float, CallerType, List[str]]:
        """Apply special reconciliation rules for LIVE calls."""
        
        reason_codes = transcript_result.reason_codes.copy()
        caller_type = voice_result.caller_type
        transcript_lower = transcript_result.transcript_text.lower()
        
        # Rule 1: AI voice but low transcript risk → uncertain
        if (voice_result.caller_type == CallerType.AI and 
            transcript_result.scam_likelihood < 30):
            caller_type = CallerType.UNCERTAIN
            final_score = min(final_score + 10, 100)
            reason_codes.append("voice_ai_low_transcript_risk")
        
        # Rule 2: Both signals suspicious → escalate strongly
        elif (voice_result.caller_type in [CallerType.AI, CallerType.UNCERTAIN] and
              transcript_result.scam_likelihood > 60):
            final_score = min(final_score + 15, 100)
            caller_type = CallerType.AI
            reason_codes.append("both_signals_suspicious")
        
        # Rule 3: Human voice but dangerous transcript → trust transcript
        elif (voice_result.caller_type == CallerType.HUMAN and
              transcript_result.scam_likelihood > 70):
            final_score = max(final_score, 75)
            caller_type = CallerType.UNCERTAIN
            reason_codes.append("human_voice_dangerous_transcript")
        
        # Rule 4: Live conversation - short victim responses
        if len(transcript_result.transcript_text.split()) < 15:
            final_score = min(final_score + 5, 100)
            reason_codes.append("short_victim_responses")
        
        # Rule 5: Urgent language detection
        if any(word in transcript_lower for word in self.URGENT_WORDS):
            final_score = min(final_score + 10, 100)
            reason_codes.append("urgent_language_detected")
        
        # Rule 6: Question pattern detection (scammer asking for info)
        if "?" in transcript_result.transcript_text:
            question_count = transcript_result.transcript_text.count("?")
            if question_count >= 3:
                final_score = min(final_score + 8, 100)
                reason_codes.append("multiple_questions_detected")
        
        # Rule 7: OTP/PIN specifically mentioned (high confidence scam)
        if "otp" in transcript_lower or "pin" in transcript_lower:
            final_score = min(final_score + 20, 100)
            reason_codes.append("otp_or_pin_mentioned")
        
        return final_score, caller_type, reason_codes
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score >= self.RISK_THRESHOLD_DANGEROUS:
            return RiskLevel.DANGEROUS
        elif score >= self.RISK_THRESHOLD_SUSPICIOUS:
            return RiskLevel.SUSPICIOUS
        else:
            return RiskLevel.SAFE
    
    def _generate_reason(
        self,
        final_risk: RiskLevel,
        final_score: float,
        caller_type: CallerType,
        voice_result: VoiceAnalysisResult,
        transcript_result: TranscriptAnalysisResult,
        reason_codes: List[str]
    ) -> str:
        """Generate human-readable decision reason."""
        
        parts = []
        
        # Main risk statement
        parts.append(f"Risk {final_risk.value} (score: {final_score:.1f}/100)")
        
        # Caller type
        parts.append(f"Caller: {caller_type.value}")
        
        # Weight explanation based on audio quality
        if voice_result.signal_quality >= self.SIGNAL_QUALITY_GOOD_THRESHOLD:
            parts.append(f"Good audio quality ({voice_result.signal_quality:.2f})")
        else:
            parts.append(f"Poor audio quality ({voice_result.signal_quality:.2f}), relying on transcript")
        
        # Top reason codes
        if reason_codes:
            top_reasons = reason_codes[:3]
            parts.append(f"Flags: {', '.join(top_reasons)}")
        
        # Transcript confidence
        if transcript_result.confidence > 0.9:
            parts.append("High transcript confidence")
        elif transcript_result.confidence < 0.7:
            parts.append("Low transcript confidence")
        
        return " | ".join(parts)
    
    def get_risk_details(self, score: float) -> dict:
        """Get detailed risk information for a score."""
        risk_level = self._get_risk_level(score)
        
        if risk_level == RiskLevel.DANGEROUS:
            severity = "CRITICAL"
            recommended_action = "Immediately block call and warn user"
            color_code = "🔴"
        elif risk_level == RiskLevel.SUSPICIOUS:
            severity = "WARNING"
            recommended_action = "Show caution warning to user"
            color_code = "🟡"
        else:
            severity = "INFO"
            recommended_action = "Normal call handling"
            color_code = "🟢"
        
        return {
            "score": score,
            "risk_level": risk_level.value,
            "severity": severity,
            "recommended_action": recommended_action,
            "color_code": color_code
        }
    
    def verify_decision_consistency(
        self,
        voice_result: VoiceAnalysisResult,
        transcript_result: TranscriptAnalysisResult
    ) -> dict:
        """Verify if voice and transcript signals are consistent."""
        
        voice_risk = voice_result.voice_score
        transcript_risk = transcript_result.scam_likelihood
        
        difference = abs(voice_risk - transcript_risk)
        
        if difference < 20:
            consistency = "HIGH"
            message = "Voice and transcript signals agree"
        elif difference < 40:
            consistency = "MEDIUM"
            message = "Some disagreement between voice and transcript"
        else:
            consistency = "LOW"
            message = "Significant disagreement - trust transcript more"
        
        return {
            "consistency": consistency,
            "difference": difference,
            "message": message,
            "voice_score": voice_risk,
            "transcript_score": transcript_risk
        }


# Quick test function
if __name__ == "__main__":
    from models import VoiceAnalysisResult, TranscriptAnalysisResult, CallerType
    
    engine = ConsensusEngine()
    
    # Test 1: Dangerous scam call
    print("\n" + "="*50)
    print("TEST 1: DANGEROUS SCAM CALL")
    print("="*50)
    
    voice = VoiceAnalysisResult(
        caller_type=CallerType.AI,
        voice_score=85.0,
        signal_quality=0.75,
        confidence=0.88
    )
    
    transcript = TranscriptAnalysisResult(
        scam_likelihood=95.0,
        reason_codes=["otp_request", "urgent_action"],
        scam_phrases_found=["OTP", "account blocked"],
        transcript_text="Your account is compromised! Share OTP immediately to secure your account.",
        confidence=0.95
    )
    
    risk, score, caller, reason, codes = engine.decide(voice, transcript)
    print(f"Risk: {risk.value}, Score: {score:.1f}")
    print(f"Reason: {reason}")
    print(f"Codes: {codes}")
    
    # Test 2: Suspicious call with poor audio
    print("\n" + "="*50)
    print("TEST 2: SUSPICIOUS CALL - POOR AUDIO")
    print("="*50)
    
    voice2 = VoiceAnalysisResult(
        caller_type=CallerType.UNCERTAIN,
        voice_score=55.0,
        signal_quality=0.35,
        confidence=0.65
    )
    
    transcript2 = TranscriptAnalysisResult(
        scam_likelihood=65.0,
        reason_codes=["prize_win"],
        scam_phrases_found=["You won"],
        transcript_text="Congratulations! You've won a free vacation. Please verify your details.",
        confidence=0.80
    )
    
    risk2, score2, caller2, reason2, codes2 = engine.decide(voice2, transcript2)
    print(f"Risk: {risk2.value}, Score: {score2:.1f}")
    print(f"Reason: {reason2}")
    
    # Test 3: Safe call
    print("\n" + "="*50)
    print("TEST 3: SAFE CALL")
    print("="*50)
    
    voice3 = VoiceAnalysisResult(
        caller_type=CallerType.HUMAN,
        voice_score=10.0,
        signal_quality=0.92,
        confidence=0.95
    )
    
    transcript3 = TranscriptAnalysisResult(
        scam_likelihood=5.0,
        reason_codes=["normal_conversation"],
        scam_phrases_found=[],
        transcript_text="Hi, this is your colleague calling about the project meeting tomorrow at 2 PM.",
        confidence=0.97
    )
    
    risk3, score3, caller3, reason3, codes3 = engine.decide(voice3, transcript3)
    print(f"Risk: {risk3.value}, Score: {score3:.1f}")
    print(f"Reason: {reason3}")