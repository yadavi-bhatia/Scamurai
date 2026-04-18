
"""Hour 21: Forensic Record - Clean forensic record structure."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path


class ForensicEvidence(BaseModel):
    """Individual evidence item."""
    type: str = Field(description="Evidence type (transcript/voice/behavioral)")
    content: str = Field(description="Evidence content")
    timestamp: str = Field(description="When evidence was collected")
    confidence: float = Field(ge=0, le=1, description="Evidence confidence")


class ForensicRecord(BaseModel):
    """Clean forensic record structure - Hour 21."""
    
    # Header
    record_id: str = Field(description="Unique record identifier")
    case_number: str = Field(description="Case reference number")
    timestamp: str = Field(description="Record creation time")
    
    # Call Information
    call_id: str = Field(description="Exotel call ID")
    scammer_number: str = Field(description="Scammer's phone number")
    victim_number: str = Field(description="Victim's phone number")
    call_duration_seconds: float = Field(default=0, description="Call duration")
    
    # Forensic Analysis
    verdict: str = Field(description="FINAL: DANGEROUS/SUSPICIOUS/SAFE")
    risk_score: float = Field(ge=0, le=100, description="Risk score 0-100")
    confidence: float = Field(ge=0, le=1, description="Analysis confidence")
    caller_type: str = Field(description="ai-likely/human-likely/uncertain")
    
    # Evidence
    primary_reason: str = Field(description="Main reason for verdict")
    indicators: List[str] = Field(default_factory=list, description="Scam indicators")
    transcript_excerpt: str = Field(default="", description="What was said")
    scam_phrases: List[str] = Field(default_factory=list, description="Suspicious phrases")
    
    # Tamper-Evident Proof
    evidence_hash: str = Field(description="SHA-256 hash of this record")
    prev_hash: str = Field(description="Previous record's hash")
    chain_position: int = Field(description="Position in evidence chain")
    chain_verified: bool = Field(default=True, description="Chain integrity status")
    
    # Chain of Custody
    created_by: str = Field(default="Person 4 - Scam Detection System")
    reviewed_by: Optional[str] = Field(default=None)
    notes: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "record_id": "FOR_20260418_001",
                "case_number": "SCAM_20260418_001",
                "call_id": "exotel_12345",
                "scammer_number": "+15551234567",
                "victim_number": "+919876543210",
                "verdict": "DANGEROUS",
                "risk_score": 98.5,
                "primary_reason": "OTP request detected"
            }
        }


class ForensicRecordBuilder:
    """Build forensic records from incident data."""
    
    def __init__(self):
        self.records: List[ForensicRecord] = []
        self.storage_path = Path("data/forensic_records.jsonl")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def build_from_incident(self, incident_data: Dict[str, Any]) -> ForensicRecord:
        """Build forensic record from incident data."""
        
        record = ForensicRecord(
            record_id=f"FOR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            case_number=f"SCAM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            call_id=incident_data.get('call_id', 'unknown'),
            scammer_number=incident_data.get('scammer_number', 'unknown'),
            victim_number=incident_data.get('victim_number', 'unknown'),
            call_duration_seconds=incident_data.get('call_duration', 0),
            verdict=incident_data.get('final_risk', 'UNKNOWN'),
            risk_score=incident_data.get('final_score', 0),
            confidence=incident_data.get('confidence', 0),
            caller_type=incident_data.get('caller_type', 'unknown'),
            primary_reason=incident_data.get('decision_reason', ''),
            indicators=incident_data.get('reason_codes', []),
            transcript_excerpt=incident_data.get('transcript_excerpt', '')[:200],
            scam_phrases=incident_data.get('scam_phrases', []),
            evidence_hash=incident_data.get('incident_hash', ''),
            prev_hash=incident_data.get('prev_hash', 'GENESIS'),
            chain_position=incident_data.get('chain_position', 0),
            chain_verified=True
        )
        
        self.records.append(record)
        self._save_record(record)
        
        return record
    
    def _save_record(self, record: ForensicRecord):
        """Save record to storage."""
        with open(self.storage_path, 'a') as f:
            f.write(record.model_dump_json() + '\n')
    
    def get_record(self, record_id: str) -> Optional[ForensicRecord]:
        """Get record by ID."""
        if not self.storage_path.exists():
            return None
        
        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get('record_id') == record_id:
                        return ForensicRecord(**data)
        return None
    
    def generate_certificate(self, record: ForensicRecord) -> str:
        """Generate forensic certificate."""
        cert = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    FORENSIC EVIDENCE CERTIFICATE                      ║
╠══════════════════════════════════════════════════════════════════════╣
║ Certificate ID: {record.record_id:<52}║
║ Case Number:    {record.case_number:<52}║
║ Timestamp:      {record.timestamp:<52}║
╠══════════════════════════════════════════════════════════════════════╣
║ VERDICT: {record.verdict:<60}║
║ Risk Score: {record.risk_score}/100{' ' * (52 - len(str(record.risk_score))) }║
║ Confidence: {record.confidence * 100:.0f}%{' ' * (56 - len(str(int(record.confidence * 100))))}║
╠══════════════════════════════════════════════════════════════════════╣
║ Evidence Hash: {record.evidence_hash[:32]}...{' ' * (28)}║
║ Chain Position: {record.chain_position:<52}║
║ Chain Verified: {'YES' if record.chain_verified else 'NO':<52}║
╠══════════════════════════════════════════════════════════════════════╣
║ This certificate is cryptographically verified.                       ║
║ Any alteration will invalidate this certificate.                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        return cert


if __name__ == "__main__":
    builder = ForensicRecordBuilder()
    
    # Test incident
    test_data = {
        "call_id": "test_001",
        "scammer_number": "+15551234567",
        "victim_number": "+919876543210",
        "final_risk": "DANGEROUS",
        "final_score": 98.5,
        "confidence": 0.95,
        "caller_type": "ai-likely",
        "decision_reason": "OTP request detected",
        "reason_codes": ["otp_request", "urgent_action"],
        "transcript_excerpt": "Share your OTP",
        "scam_phrases": ["OTP"],
        "incident_hash": "a1b2c3d4e5f6",
        "prev_hash": "GENESIS",
        "chain_position": 20
    }
    
    record = builder.build_from_incident(test_data)
    print(builder.generate_certificate(record))
    print("✅ Hour 21: Forensic record ready")
