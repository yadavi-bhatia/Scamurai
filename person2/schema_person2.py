"""
Person 2 - Frozen JSON Schema for Person 3
DO NOT MODIFY - This is the stable contract with Consensus Agent
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from enum import Enum
import json
import hashlib


class RiskLevel(str, Enum):
    """Frozen risk levels - DO NOT CHANGE"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"
    PENDING = "PENDING"


class ScamType(str, Enum):
    """Frozen scam types - DO NOT CHANGE"""
    PAYMENT_SCAM = "payment_scam"
    IDENTITY_THEFT = "identity_theft_scam"
    GOVERNMENT_IMPERSONATION = "government_impersonation"
    AUTHORITY_IMPERSONATION = "authority_impersonation"
    PRESSURE_TACTIC = "pressure_tactic"
    TECH_SUPPORT_SCAM = "tech_support_scam"
    NONE = "none"
    UNKNOWN = "unknown"


@dataclass
class FrozenDetectionResult:
    """
    FROZEN OUTPUT FOR PERSON 3 (Consensus Agent)
    This format is stable and will NOT change
    """
    # Core identifiers
    turn_id: str
    session_id: str
    timestamp: str
    
    # Transcript data
    transcript: str
    detected_keywords: List[str]
    detected_categories: List[str]
    
    # Risk assessment
    risk_score: float  # 0.0 to 1.0
    risk_level: str    # One of RiskLevel values
    scam_type: str     # One of ScamType values
    
    # Explanation for judges
    explanation: str
    reason_codes: List[str]
    
    # Evidence integrity
    evidence_hash: str
    
    # Versioning
    version: str = "2.0.0"  # FROZEN - DO NOT CHANGE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self), indent=indent)
    
    def validate(self) -> bool:
        """Validate against frozen schema rules"""
        # Check risk score range
        if not (0 <= self.risk_score <= 1):
            return False
        
        # Check risk level is valid
        valid_levels = [e.value for e in RiskLevel]
        if self.risk_level not in valid_levels:
            return False
        
        # Check scam type is valid
        valid_types = [e.value for e in ScamType]
        if self.scam_type not in valid_types:
            return False
        
        # Check version
        if self.version != "2.0.0":
            return False
        
        return True
    
    def compute_hash(self) -> str:
        """Compute evidence hash for tamper-proof logging"""
        data_string = f"{self.turn_id}|{self.session_id}|{self.transcript}|{self.risk_score}|{self.timestamp}"
        return hashlib.sha256(data_string.encode()).hexdigest()[:16]


# Adapter to convert LinguisticAgent output to frozen format
def to_frozen_format(result, session_id: str = None) -> FrozenDetectionResult:
    """
    Convert internal DetectionResult to frozen format for Person 3
    """
    # Map internal risk level to frozen enum
    risk_mapping = {
        "CRITICAL": RiskLevel.CRITICAL.value,
        "HIGH": RiskLevel.HIGH.value,
        "MEDIUM": RiskLevel.MEDIUM.value,
        "LOW": RiskLevel.LOW.value,
        "NONE": RiskLevel.NONE.value,
        "PENDING": RiskLevel.PENDING.value
    }
    
    # Map scam type to frozen enum
    type_mapping = {
        "payment_scam": ScamType.PAYMENT_SCAM.value,
        "identity_theft_scam": ScamType.IDENTITY_THEFT.value,
        "government_impersonation": ScamType.GOVERNMENT_IMPERSONATION.value,
        "authority_impersonation": ScamType.AUTHORITY_IMPERSONATION.value,
        "pressure_tactic": ScamType.PRESSURE_TACTIC.value,
        "tech_support_scam": ScamType.TECH_SUPPORT_SCAM.value,
        "none": ScamType.NONE.value,
        "unknown": ScamType.UNKNOWN.value
    }
    
    return FrozenDetectionResult(
        turn_id=getattr(result, 'turn_id', 'unknown'),
        session_id=session_id or getattr(result, 'session_id', 'unknown'),
        timestamp=getattr(result, 'timestamp', ''),
        transcript=getattr(result, 'transcript', '')[:500],
        detected_keywords=getattr(result, 'detected_keywords', [])[:10],
        detected_categories=getattr(result, 'detected_categories', []),
        risk_score=getattr(result, 'risk_score', 0.0),
        risk_level=risk_mapping.get(getattr(result, 'risk_level', 'NONE'), RiskLevel.NONE.value),
        scam_type=type_mapping.get(getattr(result, 'scam_type', 'none'), ScamType.NONE.value),
        explanation=getattr(result, 'explanation', ''),
        reason_codes=getattr(result, 'reason_codes', []),
        evidence_hash=getattr(result, 'evidence_hash', '')
    )


# Schema definition for validation
FROZEN_SCHEMA = {
    "type": "object",
    "required": [
        "turn_id", "session_id", "timestamp", "transcript",
        "detected_keywords", "detected_categories", "risk_score",
        "risk_level", "scam_type", "explanation", "reason_codes",
        "evidence_hash", "version"
    ],
    "properties": {
        "turn_id": {"type": "string", "minLength": 1},
        "session_id": {"type": "string", "minLength": 1},
        "timestamp": {"type": "string"},
        "transcript": {"type": "string"},
        "detected_keywords": {"type": "array"},
        "detected_categories": {"type": "array"},
        "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
        "risk_level": {"type": "string", "enum": [e.value for e in RiskLevel]},
        "scam_type": {"type": "string", "enum": [e.value for e in ScamType]},
        "explanation": {"type": "string"},
        "reason_codes": {"type": "array"},
        "evidence_hash": {"type": "string", "minLength": 16},
        "version": {"type": "string", "const": "2.0.0"}
    }
}


# Test the frozen format
if __name__ == "__main__":
    print("=" * 60)
    print("🔒 TESTING FROZEN JSON FORMAT")
    print("=" * 60)
    
    # Create a sample frozen result
    sample = FrozenDetectionResult(
        turn_id="session_0001",
        session_id="demo_001",
        timestamp="2026-04-18T10:30:00",
        transcript="Send me bitcoin immediately",
        detected_keywords=["bitcoin", "immediately"],
        detected_categories=["payment_request", "urgency"],
        risk_score=0.65,
        risk_level=RiskLevel.HIGH.value,
        scam_type=ScamType.PAYMENT_SCAM.value,
        explanation="💰 Payment request with urgency",
        reason_codes=["R01", "R05"],
        evidence_hash="abc123def4567890"
    )
    
    print("\n📤 Frozen Output for Person 3:")
    print(sample.to_json())
    
    print("\n✅ Schema validation:", sample.validate())
    
    print("\n" + "=" * 60)
    print("✅ Frozen format ready for Person 3")
    print("=" * 60)