
"""Unified Incident State - Combines all data sources."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

# Import your existing models
from models import (
    ExotelMetadata, 
    VoiceAnalysisResult, 
    TranscriptAnalysisResult,
    FinalDecision
)


class CallStatus(str, Enum):
    INITIATED = "initiated"
    ROUTING = "routing"
    CONNECTED = "connected"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class UnifiedIncidentState(BaseModel):
    """Single source of truth for all call data."""
    
    # Identification
    incident_id: str = Field(default="")
    call_id: str = Field(description="Exotel call ID")
    
    # Routing data (from your ExotelMetadata)
    scammer_number: str = Field(default="")
    victim_number: str = Field(default="")
    routing_path: str = Field(default="")
    
    # Voice data (from your VoiceAnalysisResult)
    caller_type: str = Field(default="unknown")
    voice_score: float = Field(default=0.0)
    signal_quality: float = Field(default=0.0)
    voice_confidence: float = Field(default=0.0)
    
    # Transcript data (from your TranscriptAnalysisResult)
    transcript_text: str = Field(default="")
    transcript_score: float = Field(default=0.0)
    scam_phrases: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    
    # Final decision (from your FinalDecision)
    final_risk: Optional[str] = Field(default=None)
    final_score: float = Field(default=0.0)
    decision_reason: str = Field(default="")
    overall_confidence: float = Field(default=0.0)
    recommended_action: str = Field(default="")
    incident_hash: str = Field(default="")
    chain_position: int = Field(default=0)
    
    # Status
    call_status: CallStatus = Field(default=CallStatus.INITIATED)
    start_time: datetime = Field(default_factory=datetime.now)
    processing_time_ms: int = Field(default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc_001",
                "call_id": "exotel_123",
                "scammer_number": "+15551234567",
                "victim_number": "+919876543210",
                "caller_type": "ai-likely",
                "final_risk": "DANGEROUS",
                "final_score": 95.5
            }
        }


class IncidentManager:
    """Manager for incident states."""
    
    def __init__(self):
        self.incidents: Dict[str, UnifiedIncidentState] = {}
    
    def create(self, call_id: str, exotel_data: ExotelMetadata) -> UnifiedIncidentState:
        """Create incident from Exotel data."""
        incident = UnifiedIncidentState(
            incident_id=f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            call_id=call_id,
            scammer_number=exotel_data.scammer_number,
            victim_number=exotel_data.victim_number,
            routing_path=exotel_data.routing_path
        )
        self.incidents[call_id] = incident
        return incident
    
    def add_voice(self, call_id: str, voice: VoiceAnalysisResult):
        """Add voice analysis."""
        if call_id in self.incidents:
            inc = self.incidents[call_id]
            inc.caller_type = voice.caller_type.value
            inc.voice_score = voice.voice_score
            inc.signal_quality = voice.signal_quality
            inc.voice_confidence = voice.confidence
    
    def add_transcript(self, call_id: str, transcript: TranscriptAnalysisResult):
        """Add transcript analysis."""
        if call_id in self.incidents:
            inc = self.incidents[call_id]
            inc.transcript_text = transcript.transcript_text
            inc.transcript_score = transcript.scam_likelihood
            inc.scam_phrases = transcript.scam_phrases_found
            inc.reason_codes = transcript.reason_codes
    
    def add_decision(self, call_id: str, decision: FinalDecision, chain_pos: int):
        """Add final decision."""
        if call_id in self.incidents:
            inc = self.incidents[call_id]
            inc.final_risk = decision.final_risk.value
            inc.final_score = decision.final_score
            inc.decision_reason = decision.decision_reason
            inc.overall_confidence = decision.confidence
            inc.recommended_action = decision.action.split()[0].lower()
            inc.incident_hash = decision.incident_hash[:16]
            inc.chain_position = chain_pos
            inc.processing_time_ms = int((datetime.now() - inc.start_time).total_seconds() * 1000)
            inc.call_status = CallStatus.COMPLETED
    
    def get(self, call_id: str) -> Optional[UnifiedIncidentState]:
        return self.incidents.get(call_id)


# Singleton
incident_manager = IncidentManager()
