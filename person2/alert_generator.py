"""
PERSON 2 - ALERT GENERATOR (Hour 27)
Judge-friendly explanation strings for alert sharing
"""

from typing import Dict, Any, List
from datetime import datetime


class AlertGenerator:
    """
    Generates judge-friendly alert messages for sharing
    Used for trusted-contact escalation and demo display
    """
    
    SEVERITY_LEVELS = {
        "DANGEROUS": {"icon": "🔴", "priority": 1, "action": "IMMEDIATE ACTION REQUIRED"},
        "SUSPICIOUS": {"icon": "🟠", "priority": 2, "action": "ESCALATE TO HUMAN"},
        "LOW_RISK": {"icon": "🟡", "priority": 3, "action": "MONITOR"},
        "SAFE": {"icon": "🟢", "priority": 4, "action": "NO ACTION"}
    }
    
    SCAM_TYPE_MESSAGES = {
        "payment_scam": "The caller is requesting payment or money transfer.",
        "identity_theft_scam": "The caller is asking for personal information (OTP, Aadhaar, bank details).",
        "government_impersonation": "The caller is pretending to be from a government agency.",
        "authority_impersonation": "The caller is impersonating a bank or tech support.",
        "pressure_tactic": "The caller is creating artificial urgency to pressure you."
    }
    
    def __init__(self):
        self.version = "1.0.0"
        print("[ALERT] Alert generator ready")
    
    def generate_alert(self, handoff: Any) -> Dict[str, Any]:
        """
        Generate a complete alert message for sharing
        
        Args:
            handoff: FinalHandoff object from LinguisticAgent
        """
        severity = self.SEVERITY_LEVELS.get(handoff.final_risk_level, self.SEVERITY_LEVELS["LOW_RISK"])
        
        # Build the alert message
        title = f"{severity['icon']} SCAM ALERT: {handoff.final_risk_level}"
        
        # Main description
        scam_explanation = self.SCAM_TYPE_MESSAGES.get(handoff.scam_type, "Suspicious scam patterns detected.")
        
        # Keywords section
        keywords_text = ""
        if handoff.detected_keywords:
            clean_keywords = [kw.replace("[MONEY]", "money").replace("[FAMILY_IMPERSONATION]", "family impersonation") 
                             for kw in handoff.detected_keywords[:5]]
            keywords_text = f"\n📝 Detected keywords: {', '.join(clean_keywords)}"
        
        # Money mention
        money_text = ""
        if handoff.money_amount_mentioned:
            money_text = "\n💰 Large money amount mentioned in the call."
        
        # Family impersonation
        family_text = ""
        if handoff.family_impersonation:
            family_text = "\n👨‍👩‍👧 Family impersonation detected - someone is pretending to be a family member."
        
        # Recommended action
        action_text = f"\n\n⚡ Recommended action: {severity['action']}"
        
        # Share instructions for high severity
        share_text = ""
        if handoff.final_risk_level in ["DANGEROUS", "SUSPICIOUS"]:
            share_text = "\n\n📱 Share this alert with trusted family members immediately."
        
        full_message = f"""{title}

{scam_explanation}{keywords_text}{money_text}{family_text}

📞 Call ID: {handoff.session_id}
🕐 Time: {handoff.timestamp}{action_text}{share_text}"""
        
        # Short version for SMS
        short_message = f"{severity['icon']} SCAM ALERT: {handoff.scam_type.replace('_', ' ').title()}. Risk: {handoff.max_risk_score:.0%}. {severity['action']}"
        
        return {
            "alert_id": hashlib.md5(f"{handoff.session_id}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
            "severity": handoff.final_risk_level,
            "severity_icon": severity["icon"],
            "title": title,
            "full_message": full_message,
            "short_message": short_message,
            "sms_ready": short_message[:160],  # SMS length limit
            "recommended_action": severity["action"],
            "share_with_family": handoff.final_risk_level in ["DANGEROUS", "SUSPICIOUS"],
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_share_payload(self, handoff: Any, contact_name: str, contact_phone: str) -> Dict[str, Any]:
        """
        Generate payload for trusted-contact sharing
        
        Used by Person 4 to send alerts to family members
        """
        alert = self.generate_alert(handoff)
        
        return {
            "to_contact": {
                "name": contact_name,
                "phone": contact_phone,
                "relationship": "trusted_contact"
            },
            "alert": alert,
            "sharing_method": "sms",  # or "whatsapp", "email", "in_app"
            "requires_confirmation": True,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    from linguistic_agent import FinalHandoff
    
    # Mock handoff for testing
    mock_handoff = FinalHandoff(
        session_id="test_123",
        timestamp=datetime.now().isoformat(),
        total_turns=5,
        max_risk_score=0.85,
        final_risk_level="DANGEROUS",
        scam_type="payment_scam",
        detected_keywords=["bitcoin", "urgent", "money"],
        detected_categories=["critical_payment", "high_urgency"],
        money_amount_mentioned=True,
        family_impersonation=False,
        summary="Payment scam with large money request",
        recommended_action="BLOCK_CALL",
        alert_message=""
    )
    
    generator = AlertGenerator()
    alert = generator.generate_alert(mock_handoff)
    print("Alert generated:")
    print(alert["full_message"])