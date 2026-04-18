"""Consensus engine combining voice and transcript signals."""

from typing import Tuple, List
from models import (
    RiskLevel, CallerType, VoiceAnalysisResult,
    TranscriptAnalysisResult
)


class ConsensusEngine:
    """Combines voice and transcript signals into final decision."""
    
    def __init__(self):
        self.RISK_THRESHOLD_SUSPICIOUS = 40
        self.RISK_THRESHOLD_DANGEROUS = 70
    
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
        if voice_result.signal_quality >= 0.7:
            transcript_weight = 0.7
            voice_weight = 0.3
        else:
            transcript_weight = 0.85
            voice_weight = 0.15
        
        final_score = (transcript_result.scam_likelihood * transcript_weight + 
                      voice_result.voice_score * voice_weight)
        
        # Step 2: Apply special reconciliation rules
        caller_type = voice_result.caller_type
        reason_codes = transcript_result.reason_codes.copy()
        
        # Rule 1: AI voice but low transcript risk -> uncertain
        if (voice_result.caller_type == CallerType.AI and 
            transcript_result.scam_likelihood < 30):
            caller_type = CallerType.UNCERTAIN
            final_score = min(final_score + 10, 100)
            reason_codes.append("voice_ai_low_transcript_risk")
        
        # Rule 2: Both suspicious -> escalate strongly
        elif (voice_result.caller_type in [CallerType.AI, CallerType.UNCERTAIN] and
              transcript_result.scam_likelihood > 60):
            final_score = min(final_score + 15, 100)
            reason_codes.append("both_signals_suspicious")
        
        # Rule 3: Determine risk level
        if final_score >= self.RISK_THRESHOLD_DANGEROUS:
            final_risk = RiskLevel.DANGEROUS
            action = "Warn user and block call"
        elif final_score >= self.RISK_THRESHOLD_SUSPICIOUS:
            final_risk = RiskLevel.SUSPICIOUS
            action = "Warn user with caution"
        else:
            final_risk = RiskLevel.SAFE
            action = "Normal handling"
        
        # Step 4: Generate reason
        reason = f"Risk {final_risk.value} (score: {final_score:.1f}) - {caller_type.value} caller"
        
        return final_risk, final_score, caller_type, reason, reason_codes
    
    def verify_decision(self, decision) -> bool:
        """Verify decision is valid."""
        return 0 <= decision.final_score <= 100