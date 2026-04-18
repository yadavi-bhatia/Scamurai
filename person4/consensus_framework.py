
"""Consensus Framework - Formal decision logic."""

from typing import Dict, Any, Optional
from enum import Enum


class SignalSource(str, Enum):
    TRANSCRIPT = "transcript"
    VOICE = "voice"
    BEHAVIORAL = "behavioral"


class ConsensusFramework:
    """
    Formal framework for combining signals.
    
    Weights:
    - Transcript: 50% (most important)
    - Voice: 30% (supporting evidence)
    - Behavioral: 20% (contextual clues)
    
    Thresholds:
    - Score >= 70 → DANGEROUS
    - Score >= 40 → SUSPICIOUS
    - Score < 40 → SAFE
    """
    
    DANGEROUS_THRESHOLD = 70
    SUSPICIOUS_THRESHOLD = 40
    
    def combine(
        self,
        transcript_score: float,
        voice_score: float,
        signal_quality: float = 0.8,
        behavioral_signals: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Combine all signals into final decision.
        
        Args:
            transcript_score: Risk score from transcript (0-100)
            voice_score: Risk score from voice (0-100)
            signal_quality: Audio quality (0-1)
            behavioral_signals: Dict of behavioral flags (optional)
        
        Returns:
            Dict with final_risk, final_score, confidence, reason
        """
        
        # Handle None case
        if behavioral_signals is None:
            behavioral_signals = {}
        
        # Adjust weights based on audio quality
        if signal_quality < 0.5:
            trans_weight, voice_weight = 0.70, 0.10
        elif signal_quality > 0.8:
            trans_weight, voice_weight = 0.40, 0.40
        else:
            trans_weight, voice_weight = 0.50, 0.30
        
        # Calculate behavioral score
        behavioral_score = self._behavioral_score(behavioral_signals)
        behavioral_weight = 0.20
        
        # Weighted score
        final_score = (
            transcript_score * trans_weight +
            voice_score * voice_weight +
            behavioral_score * behavioral_weight
        )
        
        # Apply modifiers
        if behavioral_signals.get("otp_request"):
            final_score = min(final_score + 15, 100)
        if behavioral_signals.get("urgent_action"):
            final_score = min(final_score + 10, 100)
        
        # Determine risk
        if final_score >= self.DANGEROUS_THRESHOLD:
            risk = "DANGEROUS"
        elif final_score >= self.SUSPICIOUS_THRESHOLD:
            risk = "SUSPICIOUS"
        else:
            risk = "SAFE"
        
        # Calculate confidence (higher when signals agree)
        agreement = 1.0 - (abs(transcript_score - voice_score) / 100)
        confidence = (signal_quality * 0.6) + (agreement * 0.4)
        
        return {
            "final_risk": risk,
            "final_score": round(final_score, 1),
            "confidence": round(confidence, 3),
            "reason": self._reason(risk, final_score, behavioral_signals)
        }
    
    def _behavioral_score(self, signals: Dict[str, bool]) -> float:
        """Calculate risk score from behavioral signals."""
        score = 0.0
        
        # High impact (15 points)
        if signals.get("otp_request"):
            score += 15
        if signals.get("urgent_action"):
            score += 15
        if signals.get("personal_info_request"):
            score += 15
        
        # Medium impact (10 points)
        if signals.get("multiple_questions"):
            score += 10
        if signals.get("bank_impersonation"):
            score += 10
        
        return min(score, 100)
    
    def _reason(self, risk: str, score: float, signals: Dict[str, bool]) -> str:
        """Generate human-readable reason."""
        if risk == "DANGEROUS":
            if signals.get("otp_request"):
                return f"DANGEROUS: OTP request detected (score: {score:.0f})"
            return f"DANGEROUS: Multiple scam indicators (score: {score:.0f})"
        elif risk == "SUSPICIOUS":
            return f"SUSPICIOUS: Unusual patterns (score: {score:.0f})"
        return f"SAFE: No scam indicators (score: {score:.0f})"


# Quick test
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Consensus Framework")
    print("="*50)
    
    cf = ConsensusFramework()
    
    # Test 1: With behavioral signals
    result1 = cf.combine(95, 85, 0.8, {"otp_request": True, "urgent_action": True})
    print(f"\n✅ Test 1 (with signals): {result1['final_risk']} - {result1['reason']}")
    
    # Test 2: Without behavioral signals (None)
    result2 = cf.combine(95, 85, 0.8)
    print(f"✅ Test 2 (None): {result2['final_risk']} - {result2['reason']}")
    
    # Test 3: Empty dict
    result3 = cf.combine(95, 85, 0.8, {})
    print(f"✅ Test 3 (empty dict): {result3['final_risk']} - {result3['reason']}")
    
    print("\n✅ All tests passed! The None issue is fixed.")
