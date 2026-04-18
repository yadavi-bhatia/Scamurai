
"""Dashboard Contract - What the frontend displays."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    DANGEROUS = "DANGEROUS"


class DashboardPayload(BaseModel):
    """Format for frontend display."""
    
    # Call info
    incident_id: str
    call_id: str
    
    # Risk display
    risk_level: RiskLevel
    risk_score: float
    risk_color: str  # red, orange, green
    risk_icon: str   # alert-triangle, alert-circle, check-circle
    
    # Confidence
    confidence_percentage: int
    confidence_level: str  # HIGH, MEDIUM, LOW
    
    # Caller
    caller_type: str
    scammer_number: str  # masked
    victim_number: str   # masked
    
    # Evidence
    evidence_hash: str
    chain_verified: bool
    
    # Decision
    decision_reason: str
    reason_codes: List[str]
    scam_phrases: List[str]
    transcript_preview: str
    
    # Action
    recommended_action: str  # block, warn, allow
    user_warning: str
    
    # Metadata
    timestamp: str
    processing_time_ms: int


def create_dashboard(incident) -> DashboardPayload:
    """Create dashboard payload from incident state."""
    
    # Colors based on risk
    if incident.final_risk == "DANGEROUS":
        risk_color = "red"
        risk_icon = "alert-triangle"
    elif incident.final_risk == "SUSPICIOUS":
        risk_color = "orange"
        risk_icon = "alert-circle"
    else:
        risk_color = "green"
        risk_icon = "check-circle"
    
    # Confidence level
    if incident.overall_confidence >= 0.8:
        confidence_level = "HIGH"
    elif incident.overall_confidence >= 0.6:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"
    
    # Mask phone numbers
    scammer_masked = incident.scammer_number[:4] + "****" + incident.scammer_number[-2:] if len(incident.scammer_number) > 6 else incident.scammer_number
    victim_masked = incident.victim_number[:4] + "****" + incident.victim_number[-2:] if len(incident.victim_number) > 6 else incident.victim_number
    
    # Warning message
    if incident.final_risk == "DANGEROUS":
        warning = "⚠️ DANGER: Do NOT share OTP, PIN, or passwords!"
    elif incident.final_risk == "SUSPICIOUS":
        warning = "⚠️ CAUTION: Verify caller identity before sharing information"
    else:
        warning = "ℹ️ Call appears safe. Always verify suspicious requests."
    
    return DashboardPayload(
        incident_id=incident.incident_id,
        call_id=incident.call_id,
        risk_level=RiskLevel(incident.final_risk) if incident.final_risk else RiskLevel.SAFE,
        risk_score=incident.final_score,
        risk_color=risk_color,
        risk_icon=risk_icon,
        confidence_percentage=int(incident.overall_confidence * 100),
        confidence_level=confidence_level,
        caller_type=incident.caller_type,
        scammer_number=scammer_masked,
        victim_number=victim_masked,
        evidence_hash=incident.incident_hash[:16],
        chain_verified=True,
        decision_reason=incident.decision_reason,
        reason_codes=incident.reason_codes[:5],
        scam_phrases=incident.scam_phrases[:5],
        transcript_preview=incident.transcript_text[:150] + "..." if len(incident.transcript_text) > 150 else incident.transcript_text,
        recommended_action=incident.recommended_action,
        user_warning=warning,
        timestamp=datetime.now().isoformat(),
        processing_time_ms=incident.processing_time_ms
    )
