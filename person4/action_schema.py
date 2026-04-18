
"""Hour 24: Action Schema - Define incident actions for block, report, and trusted contact."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions that can be taken."""
    BLOCK = "block"
    REPORT = "report"
    TRUSTED_ALERT = "trusted_alert"
    WHITELIST = "whitelist"
    REVIEW = "review"


class ActionPriority(str, Enum):
    """Priority levels for actions."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class BlockAction(BaseModel):
    """Schema for block action."""
    action_type: ActionType = ActionType.BLOCK
    phone_number: str
    reason: str
    verdict: str
    risk_score: float
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str = "default_user"
    permanent: bool = True


class ReportAction(BaseModel):
    """Schema for report action (shared reputation)."""
    action_type: ActionType = ActionType.REPORT
    phone_number: str
    verdict: str
    tags: List[str]
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "system"
    user_id: Optional[str] = None


class TrustedAlertAction(BaseModel):
    """Schema for trusted contact alert action."""
    action_type: ActionType = ActionType.TRUSTED_ALERT
    phone_number: str
    scam_category: str
    reason: str
    amount_at_risk: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    contact_ids: List[str]
    user_id: str = "default_user"
    severity: str = "high"


class IncidentAction(BaseModel):
    """Complete incident action combining all action types."""
    incident_id: str
    call_id: str
    actions: List[Dict[str, Any]]
    priority: ActionPriority
    executed_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"


class ActionResponse(BaseModel):
    """Response after executing actions."""
    success: bool
    action_type: ActionType
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


# Action factory to create action schemas
class ActionFactory:
    """Factory to create action schemas from decision output."""
    
    @staticmethod
    def create_block_action(caller_number: str, verdict: str, risk_score: float, reason: str) -> BlockAction:
        return BlockAction(
            phone_number=caller_number,
            reason=reason,
            verdict=verdict,
            risk_score=risk_score
        )
    
    @staticmethod
    def create_report_action(caller_number: str, verdict: str, tags: List[str], confidence: float) -> ReportAction:
        return ReportAction(
            phone_number=caller_number,
            verdict=verdict,
            tags=tags,
            confidence=confidence
        )
    
    @staticmethod
    def create_trusted_alert(caller_number: str, category: str, reason: str, amount: Optional[float], contact_ids: List[str]) -> TrustedAlertAction:
        return TrustedAlertAction(
            phone_number=caller_number,
            scam_category=category,
            reason=reason,
            amount_at_risk=amount,
            contact_ids=contact_ids
        )


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 24: Action Schema")
    print("="*50)
    
    # Test block action
    block = ActionFactory.create_block_action("+15551234567", "DANGEROUS", 95, "OTP request")
    print(f"✅ Block Action: {block.action_type} - {block.phone_number}")
    
    # Test report action
    report = ActionFactory.create_report_action("+15551234567", "DANGEROUS", ["otp_request"], 0.95)
    print(f"✅ Report Action: {report.action_type} - {report.phone_number}")
    
    # Test alert action
    alert = ActionFactory.create_trusted_alert("+15551234567", "Bank Fraud", "OTP request", 50000, ["contact_1"])
    print(f"✅ Alert Action: {alert.action_type} - {alert.scam_category}")
    
    print("\n✅ Hour 24 Complete: Action schema ready!")
