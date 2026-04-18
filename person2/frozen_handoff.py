"""
Hour 20: Freeze Transcript Module
Stable handoff format for Person 3 (Consensus Agent)
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Import our stable components
from reason_codes import ReasonCodeGenerator
from summary_generator import SummaryGenerator
from schema_validator import StableOutput, SchemaValidator


@dataclass
class FrozenHandoff:
    """
    FROZEN HANDOFF FOR PERSON 3
    This format is stable and will NOT change after hour 20
    """
    # Session identification
    session_id: str
    call_id: str
    timestamp: str
    
    # Detection results
    turns_analyzed: int
    max_risk_score: float
    final_risk_level: str  # SAFE, LOW_RISK, SUSPICIOUS, DANGEROUS
    
    # Detailed findings
    scam_type: str
    detected_keywords: List[str]
    detected_categories: List[str]
    reason_codes: List[str]
    
    # Explanations
    short_summary: str
    detailed_explanation: str
    
    # Evidence
    evidence_hashes: List[str]
    
    # For Person 3 decision
    recommended_action: str  # BLOCK, ESCALATE, MONITOR, NONE
    
    # Version
    version: str = "2.0.0"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent)


class FrozenHandoffGenerator:
    """
    Generates frozen handoff for Person 3
    This is the ONLY interface Person 3 should use
    """
    
    def __init__(self):
        self.reason_generator = ReasonCodeGenerator()
        self.summary_generator = SummaryGenerator()
        self.schema_validator = SchemaValidator()
    
    def create_handoff(self, 
                       session_id: str,
                       call_id: str,
                       detection_results: List[Dict[str, Any]]) -> FrozenHandoff:
        """
        Create a frozen handoff from detection results
        
        Args:
            session_id: Unique session identifier
            call_id: Call identifier from Exotel
            detection_results: List of detection results from analyze_transcript
        
        Returns:
            FrozenHandoff object ready for Person 3
        """
        if not detection_results:
            return self._empty_handoff(session_id, call_id)
        
        # Find highest risk
        max_result = max(detection_results, key=lambda x: x.get("risk_score", 0))
        max_risk = max_result.get("risk_score", 0)
        
        # Collect all keywords and categories
        all_keywords = set()
        all_categories = set()
        evidence_hashes = []
        
        for r in detection_results:
            all_keywords.update(r.get("detected_keywords", []))
            all_categories.update(r.get("detected_categories", []))
            if r.get("evidence_hash"):
                evidence_hashes.append(r["evidence_hash"])
        
        # Determine final risk level (for Person 3)
        if max_risk >= 0.6:
            final_risk = "DANGEROUS"
            action = "BLOCK"
        elif max_risk >= 0.4:
            final_risk = "SUSPICIOUS"
            action = "ESCALATE"
        elif max_risk >= 0.1:
            final_risk = "LOW_RISK"
            action = "MONITOR"
        else:
            final_risk = "SAFE"
            action = "NONE"
        
        # Generate reason codes
        reason_codes = self.reason_generator.generate(
            list(all_categories), 
            list(all_keywords)
        )
        
        # Generate summaries
        short_summary = self.summary_generator.generate_turn_summary(max_result)
        detailed_explanation = max_result.get("explanation", "")
        
        # Determine scam type
        scam_type = max_result.get("scam_type", "none")
        if scam_type == "none" and max_risk < 0.1:
            scam_type = "none"
        
        return FrozenHandoff(
            session_id=session_id,
            call_id=call_id,
            timestamp=datetime.now().isoformat(),
            turns_analyzed=len(detection_results),
            max_risk_score=round(max_risk, 3),
            final_risk_level=final_risk,
            scam_type=scam_type,
            detected_keywords=list(all_keywords)[:10],
            detected_categories=list(all_categories),
            reason_codes=reason_codes[:5],
            short_summary=short_summary,
            detailed_explanation=detailed_explanation,
            evidence_hashes=evidence_hashes[:5],
            recommended_action=action,
            version="2.0.0"
        )
    
    def _empty_handoff(self, session_id: str, call_id: str) -> FrozenHandoff:
        """Create empty handoff when no results"""
        return FrozenHandoff(
            session_id=session_id,
            call_id=call_id,
            timestamp=datetime.now().isoformat(),
            turns_analyzed=0,
            max_risk_score=0.0,
            final_risk_level="SAFE",
            scam_type="none",
            detected_keywords=[],
            detected_categories=[],
            reason_codes=[],
            short_summary="No analysis data available",
            detailed_explanation="No transcript chunks were analyzed",
            evidence_hashes=[],
            recommended_action="NONE",
            version="2.0.0"
        )
    
    def validate_handoff(self, handoff: FrozenHandoff) -> tuple[bool, List[str]]:
        """Validate handoff against frozen schema"""
        return self.schema_validator.validate_output(handoff.to_dict())


# Test the frozen handoff
if __name__ == "__main__":
    print("=" * 60)
    print("🔒 HOUR 20: FREEZE TRANSCRIPT MODULE")
    print("Stable Handoff for Person 3")
    print("=" * 60)
    
    generator = FrozenHandoffGenerator()
    
    # Simulate detection results
    sample_results = [
        {
            "risk_score": 0.0,
            "risk_level": "NONE",
            "detected_keywords": [],
            "detected_categories": [],
            "scam_type": "none",
            "explanation": "Normal conversation",
            "evidence_hash": "hash1"
        },
        {
            "risk_score": 0.65,
            "risk_level": "HIGH",
            "detected_keywords": ["bitcoin", "immediately"],
            "detected_categories": ["payment_request", "urgency"],
            "scam_type": "payment_scam",
            "explanation": "Payment request with urgency",
            "evidence_hash": "hash2"
        }
    ]
    
    # Create handoff
    handoff = generator.create_handoff(
        session_id="demo_001",
        call_id="EXOTEL_12345",
        detection_results=sample_results
    )
    
    print("\n📤 FROZEN HANDOFF FOR PERSON 3:")
    print(handoff.to_json())
    
    # Validate
    valid, errors = generator.validate_handoff(handoff)
    print(f"\n✅ Schema Validation: {'PASSED' if valid else 'FAILED'}")
    
    if errors:
        for error in errors:
            print(f"   Error: {error}")
    
    print("\n" + "=" * 60)
    print("✅ Person 2 Module FROZEN - Ready for Person 3")
    print("   Version: 2.0.0")
    print("   Schema: Stable")
    print("   Handoff: Ready")
    print("=" * 60)