
"""Hour 27: Alert Payload - Trusted-contact alert message format."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AlertChannel(str, Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    EMAIL = "email"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QuickAction(str, Enum):
    CALL_BACK = "call_back_together"
    WARN_CONTACT = "warn_contact"
    MARK_SAFE = "mark_safe"
    BLOCK_NUMBER = "block_number"


class TrustedAlertPayload(BaseModel):
    """
    Hour 27: Alert Payload Schema
    Format for trusted-contact alerts sent via SMS/WhatsApp/In-app.
    """
    alert_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Call information
    caller_number: str
    scam_category: str
    reason: str
    amount_at_risk: Optional[float] = None
    time_of_call: str
    
    # Alert metadata
    severity: AlertSeverity
    requires_action: bool = True
    
    # Quick actions for the contact
    quick_actions: List[QuickAction] = [
        QuickAction.CALL_BACK,
        QuickAction.WARN_CONTACT,
        QuickAction.MARK_SAFE
    ]
    
    # Sharing channels
    channels: List[AlertChannel] = [AlertChannel.SMS, AlertChannel.WHATSAPP]
    
    def to_sms_format(self) -> str:
        """Convert to SMS-friendly format."""
        message = f"🚨 POSSIBLE SCAM ALERT!\n"
        message += f"📞 Caller: {self.caller_number}\n"
        message += f"⚠️ Type: {self.scam_category}\n"
        message += f"📝 Reason: {self.reason}\n"
        message += f"🕐 Time: {self.time_of_call}\n"
        
        if self.amount_at_risk and self.amount_at_risk > 0:
            message += f"💰 Amount: ₹{self.amount_at_risk:,.2f}\n"
        
        message += f"\nQuick actions:\n"
        message += f"• Call me back\n"
        message += f"• Warn me about this number\n"
        message += f"• Mark as safe"
        
        return message
    
    def to_whatsapp_format(self) -> str:
        """Convert to WhatsApp-friendly format with emojis."""
        message = f"🚨 *POSSIBLE SCAM ALERT!*\n\n"
        message += f"📞 *Caller:* {self.caller_number}\n"
        message += f"⚠️ *Type:* {self.scam_category}\n"
        message += f"📝 *Reason:* {self.reason}\n"
        message += f"🕐 *Time:* {self.time_of_call}\n"
        
        if self.amount_at_risk and self.amount_at_risk > 0:
            message += f"💰 *Amount at risk:* ₹{self.amount_at_risk:,.2f}\n"
        
        message += f"\n*Quick actions:*\n"
        message += f"1️⃣ Call me back together\n"
        message += f"2️⃣ Warn me about this number\n"
        message += f"3️⃣ Mark as safe"
        
        return message
    
    def to_inapp_format(self) -> Dict[str, Any]:
        """Convert to in-app notification format."""
        return {
            "title": "🚨 Possible Scam Alert!",
            "body": f"Call from {self.caller_number} - {self.scam_category}",
            "data": {
                "caller_number": self.caller_number,
                "scam_category": self.scam_category,
                "reason": self.reason,
                "amount_at_risk": self.amount_at_risk,
                "alert_id": self.alert_id
            },
            "actions": [a.value for a in self.quick_actions]
        }
    
    def to_email_format(self) -> str:
        """Convert to email format."""
        subject = f"🚨 Possible Scam Alert - {self.scam_category}"
        
        body = f"""
Dear Trusted Contact,

A possible scam call has been detected involving someone you know.

CALL DETAILS:
- Caller Number: {self.caller_number}
- Scam Type: {self.scam_category}
- Reason: {self.reason}
- Time: {self.time_of_call}
"""
        if self.amount_at_risk and self.amount_at_risk > 0:
            body += f"- Amount at Risk: ₹{self.amount_at_risk:,.2f}\n"
        
        body += f"""
QUICK ACTIONS:
1. Call them back immediately
2. Warn them about this number
3. Mark as safe if you recognize it

Stay safe!
- Scam Detection System
"""
        return f"Subject: {subject}\n\n{body}"


class AlertPayloadFactory:
    """Factory to create alert payloads from decision data."""
    
    @staticmethod
    def create_from_decision(
        caller_number: str,
        verdict: str,
        reason: str,
        detected_amount: Optional[float],
        scam_tags: List[str]
    ) -> TrustedAlertPayload:
        """Create alert payload from decision output."""
        
        # Determine scam category from tags
        if "bank_impersonation" in scam_tags or "otp_request" in scam_tags:
            category = "Bank Fraud"
        elif "family_impersonation" in scam_tags:
            category = "Family Impersonation"
        elif "prize_win" in scam_tags:
            category = "Prize Scam"
        else:
            category = "Suspicious Call"
        
        # Determine severity
        if detected_amount and detected_amount >= 50000:
            severity = AlertSeverity.CRITICAL
        elif verdict == "DANGEROUS":
            severity = AlertSeverity.HIGH
        else:
            severity = AlertSeverity.MEDIUM
        
        return TrustedAlertPayload(
            alert_id=f"alt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            caller_number=caller_number,
            scam_category=category,
            reason=reason,
            amount_at_risk=detected_amount,
            time_of_call=datetime.now().strftime("%I:%M %p"),
            severity=severity
        )


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 27: Alert Payload")
    print("="*50)
    
    # Create alert payload
    payload = AlertPayloadFactory.create_from_decision(
        caller_number="+15551234567",
        verdict="DANGEROUS",
        reason="OTP request with urgent language",
        detected_amount=100000,
        scam_tags=["otp_request", "bank_impersonation"]
    )
    
    print(f"✅ Alert ID: {payload.alert_id}")
    print(f"✅ Severity: {payload.severity.value}")
    
    print("\n--- SMS Format ---")
    print(payload.to_sms_format())
    
    print("\n--- WhatsApp Format ---")
    print(payload.to_whatsapp_format())
    
    print("\n✅ Hour 27 Complete: Alert payload ready!")
