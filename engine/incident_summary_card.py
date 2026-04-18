
"""Hour 35: Incident Summary Card - Clean summary for demo presentation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class IncidentSummaryCard(BaseModel):
    """Clean summary card showing verdict, actions, and share status."""
    
    # Header
    incident_id: str
    timestamp: str
    call_id: str
    
    # Verdict
    verdict: str
    verdict_icon: str
    risk_score: int
    confidence: float
    
    # Caller Info
    caller_number: str
    caller_type: str
    
    # Detection
    primary_reason: str
    indicators: List[str]
    transcript_excerpt: str
    
    # Actions Taken
    blocked: bool
    reported_to_community: bool
    trusted_alert_sent: bool
    alert_contacts: List[str]
    
    # Evidence
    evidence_hash: str
    chain_position: int
    chain_verified: bool
    
    # Demo Display
    user_instruction: str


def create_demo_summary(
    incident_id: str = "DEMO_001",
    call_id: str = "CALL_001",
    verdict: str = "DANGEROUS",
    risk_score: int = 98,
    caller_number: str = "+15551234567",
    blocked: bool = True,
    reported: bool = True,
    alert_sent: bool = True,
    contacts: List[str] = None
) -> IncidentSummaryCard:
    """Create a demo-ready incident summary card."""
    
    if contacts is None:
        contacts = ["Mom", "Dad"]
    
    # Determine icon
    if verdict == "DANGEROUS":
        icon = "🔴"
        instruction = "⚠️ DO NOT share OTP, PIN, or passwords! Block immediately."
    elif verdict == "SUSPICIOUS":
        icon = "🟡"
        instruction = "⚠️ Verify caller identity before sharing information."
    else:
        icon = "🟢"
        instruction = "ℹ️ Call appears safe. Always verify suspicious requests."
    
    return IncidentSummaryCard(
        incident_id=incident_id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        call_id=call_id,
        verdict=verdict,
        verdict_icon=icon,
        risk_score=risk_score,
        confidence=0.95,
        caller_number=caller_number,
        caller_type="ai-likely",
        primary_reason="OTP request detected with urgent language",
        indicators=["otp_request", "urgent_action", "bank_impersonation"],
        transcript_excerpt="Your account is compromised. Share the OTP sent to your phone immediately.",
        blocked=blocked,
        reported_to_community=reported,
        trusted_alert_sent=alert_sent,
        alert_contacts=contacts,
        evidence_hash="a1b2c3d4e5f67890",
        chain_position=42,
        chain_verified=True,
        user_instruction=instruction
    )


def print_summary_card(card: IncidentSummaryCard):
    """Print a beautiful summary card for demo."""
    
    print("\n" + "="*70)
    print(f"{card.verdict_icon} INCIDENT SUMMARY CARD")
    print("="*70)
    
    print(f"\n📋 INCIDENT ID: {card.incident_id}")
    print(f"🕐 TIME: {card.timestamp}")
    print(f"📞 CALL ID: {card.call_id}")
    
    print(f"\n🎯 VERDICT: {card.verdict_icon} {card.verdict}")
    print(f"📊 RISK SCORE: {card.risk_score}/100")
    print(f"📈 CONFIDENCE: {card.confidence:.1%}")
    
    print(f"\n📞 CALLER: {card.caller_number}")
    print(f"🤖 CALLER TYPE: {card.caller_type}")
    
    print(f"\n🔍 PRIMARY REASON: {card.primary_reason}")
    print(f"📝 INDICATORS: {', '.join(card.indicators)}")
    
    print(f"\n📝 TRANSCRIPT EXCERPT:")
    print(f"   \"{card.transcript_excerpt}\"")
    
    print(f"\n✅ ACTIONS TAKEN:")
    print(f"   🚫 Blocked: {'✅' if card.blocked else '❌'}")
    print(f"   🌍 Reported to Community: {'✅' if card.reported_to_community else '❌'}")
    print(f"   👥 Trusted Alert Sent: {'✅' if card.trusted_alert_sent else '❌'}")
    
    if card.alert_contacts:
        print(f"   📱 Alerted Contacts: {', '.join(card.alert_contacts)}")
    
    print(f"\n🔒 FORENSIC EVIDENCE:")
    print(f"   Evidence Hash: {card.evidence_hash}")
    print(f"   Chain Position: {card.chain_position}")
    print(f"   Chain Verified: {'✅ YES' if card.chain_verified else '❌ NO'}")
    
    print(f"\n💡 USER INSTRUCTION: {card.user_instruction}")
    
    print("\n" + "="*70)
    print("✅ INCIDENT CLOSED - EVIDENCE SECURED")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("HOUR 35: Incident Summary Card")
    print("="*60)
    
    # Create and display demo summary
    card = create_demo_summary()
    print_summary_card(card)
    
    print("✅ Hour 35 Complete: Incident summary card ready for demo!")
