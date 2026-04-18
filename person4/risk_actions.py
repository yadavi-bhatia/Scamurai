
"""Post-Call Risk Action Module - Core Decision Logic."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskDecision:
    action_taken: str
    blocklist_updated: bool
    shared_list_updated: bool
    trusted_contact_prompt_shown: bool
    severity: str
    explanation: str
    next_steps: List[str]
    tags: List[str] = field(default_factory=list)
    needs_review: bool = False


class RiskActionEngine:
    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 40
    HIGH_VALUE_THRESHOLD = 50000
    
    def __init__(self):
        self.stats = {
            "total_processed": 0,
            "blocked": 0,
            "reported": 0,
            "trusted_alerts": 0,
            "needs_review": 0
        }
    
    def decide(self, call_id: str, caller_number: str, verdict: str, risk_score: float,
               scam_tags: List[str], transcript_summary: str, detected_amount: Optional[float] = None,
               family_impersonation_flag: bool = False, deepfake_flag: bool = False,
               user_trusted_contacts: List[Dict] = None, user_preferences: Dict = None) -> RiskDecision:
        
        self.stats["total_processed"] += 1
        
        # Calculate severity
        if risk_score >= 90 or (detected_amount and detected_amount >= self.HIGH_VALUE_THRESHOLD * 2):
            severity = Severity.CRITICAL
        elif risk_score >= 70 or (detected_amount and detected_amount >= self.HIGH_VALUE_THRESHOLD):
            severity = Severity.HIGH
        elif risk_score >= 40 or family_impersonation_flag or deepfake_flag:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW
        
        blocklist_updated = False
        shared_list_updated = False
        trusted_prompt = False
        action_taken = "none"
        next_steps = []
        needs_review = False
        
        if verdict == "DANGEROUS" and risk_score >= self.HIGH_RISK_THRESHOLD:
            blocklist_updated = True
            shared_list_updated = True
            action_taken = "blocked_and_reported"
            self.stats["blocked"] += 1
            self.stats["reported"] += 1
            next_steps.append("Number added to your blocklist")
            next_steps.append("Reported to community spam list")
        
        if severity in [Severity.HIGH, Severity.CRITICAL]:
            trusted_prompt = True
            self.stats["trusted_alerts"] += 1
            next_steps.insert(0, "Share alert with trusted contacts")
            if detected_amount and detected_amount >= self.HIGH_VALUE_THRESHOLD:
                next_steps.insert(0, f"Large amount detected: ₹{detected_amount:,.2f}")
        
        explanation = f"Scam detected with {risk_score:.0f}% confidence. {severity.value.upper()} severity."
        
        return RiskDecision(
            action_taken=action_taken,
            blocklist_updated=blocklist_updated,
            shared_list_updated=shared_list_updated,
            trusted_contact_prompt_shown=trusted_prompt,
            severity=severity.value,
            explanation=explanation,
            next_steps=next_steps,
            tags=scam_tags,
            needs_review=needs_review
        )
    
    def get_stats(self):
        return self.stats


print("✅ risk_actions.py ready")
