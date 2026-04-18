"""Data models for Person 4 - Consensus Agent."""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Final risk levels."""
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    DANGEROUS = "DANGEROUS"


class CallerType(str, Enum):
    """Detected caller type."""
    HUMAN = "human-likely"
    AI = "ai-likely"
    UNCERTAIN = "uncertain"


class VoiceAnalysisResult(BaseModel):
    """Output from Person 2 (voice agent)."""
    caller_type: CallerType
    voice_score: float = Field(ge=0, le=100, description="Voice similarity score (0-100)")
    signal_quality: float = Field(ge=0, le=1, description="Audio quality (0-1)")
    confidence: float = Field(ge=0, le=1, description="Confidence in voice analysis")
    raw_features: Optional[dict] = Field(default=None, description="Raw voice features")


class TranscriptAnalysisResult(BaseModel):
    """Output from Person 3 (linguistic agent)."""
    scam_likelihood: float = Field(ge=0, le=100, description="Likelihood of scam (0-100)")
    reason_codes: List[str] = Field(default_factory=list, description="Codes explaining why flagged")
    scam_phrases_found: List[str] = Field(default_factory=list, description="Scam phrases detected")
    transcript_text: str = Field(default="", description="Call transcript text")
    confidence: float = Field(ge=0, le=1, description="Confidence in transcript analysis")


class ExotelMetadata(BaseModel):
    """Routing metadata from Exotel (Person 1)."""
    call_id: str = Field(description="Unique call identifier from Exotel")
    stream_id: str = Field(description="Stream identifier for audio")
    timestamp: datetime = Field(default_factory=datetime.now, description="When call was received")
    routing_path: str = Field(description="Routing path (exotel→victim_phone)")
    victim_number: str = Field(description="Victim's phone number")
    scammer_number: str = Field(description="Scammer's phone number")
    transfer_status: str = Field(default="connected", description="Call transfer status")
    call_duration: Optional[float] = Field(default=None, description="Duration of call in seconds")


class FinalDecision(BaseModel):
    """Final output from consensus agent."""
    # Risk assessment
    final_risk: RiskLevel = Field(description="Final risk level")
    final_score: float = Field(ge=0, le=100, description="Risk score (0-100)")
    caller_type: CallerType = Field(description="Classified caller type")
    decision_reason: str = Field(description="Human-readable reason for decision")
    confidence: float = Field(ge=0, le=1, description="Overall confidence in decision")
    reason_codes: List[str] = Field(default_factory=list, description="Detailed reason codes")
    transcript_excerpt: str = Field(default="", description="First 200 chars of transcript")
    
    # Forensic evidence
    incident_hash: str = Field(default="", description="SHA-256 hash of this incident")
    prev_hash: str = Field(default="", description="Previous incident's hash for chain")
    timestamp: datetime = Field(default_factory=datetime.now, description="When decision was made")
    
    # Response actions
    action: str = Field(description="Action to take (block/warn/allow)")
    trigger_red_alert: bool = Field(default=False, description="Whether to show red alert")
    trigger_hold_music: bool = Field(default=False, description="Whether to play hold music")
    
    class Config:
        json_schema_extra = {
            "example": {
                "final_risk": "DANGEROUS",
                "final_score": 95.5,
                "caller_type": "ai-likely",
                "decision_reason": "High scam probability detected",
                "confidence": 0.92,
                "reason_codes": ["otp_request", "urgent_action"],
                "transcript_excerpt": "Share your OTP to secure your account...",
                "action": "Warn user and block call",
                "trigger_red_alert": True,
                "trigger_hold_music": True
            }
        }