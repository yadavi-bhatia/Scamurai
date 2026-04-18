
"""Judge Summary - Final output for demo presentation."""

from datetime import datetime
from typing import List
from pydantic import BaseModel


class JudgeSummary(BaseModel):
    """Complete summary for judge/demo audience."""
    
    # Header
    incident_id: str
    timestamp: str
    
    # Verdict (BIG and clear)
    verdict: str
    verdict_icon: str
    risk_score: int
    
    # Detection
    caller_type: str
    primary_reason: str
    indicators: List[str]
    
    # Evidence
    transcript_excerpt: str
    scam_phrases: List[str]
    
    # Call info
    caller_number: str
    victim_number: str
    call_duration: str
    
    # Forensic proof
    evidence_hash: str
    chain_verified: bool
    
    # Action taken
    action_taken: str
    user_instruction: str


def create_judge_summary(incident, duration_seconds: float) -> JudgeSummary:
    """Create judge summary from incident state."""
    
    # Verdict icon
    if incident.final_risk == "DANGEROUS":
        icon = "🔴"
    elif incident.final_risk == "SUSPICIOUS":
        icon = "🟡"
    else:
        icon = "🟢"
    
    # Format duration
    mins = int(duration_seconds // 60)
    secs = int(duration_seconds % 60)
    duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
    
    # Action and instruction
    if incident.final_risk == "DANGEROUS":
        action = "BLOCKED + Hold Music Trap"
        instruction = "⚠️ NEVER share OTP, PIN, or passwords"
    elif incident.final_risk == "SUSPICIOUS":
        action = "WARNING Displayed"
        instruction = "⚠️ Verify caller identity before sharing information"
    else:
        action = "ALLOWED - Normal Handling"
        instruction = "ℹ️ Call appears safe. Always verify suspicious requests"
    
    return JudgeSummary(
        incident_id=incident.incident_id,
        timestamp=incident.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        verdict=incident.final_risk or "UNKNOWN",
        verdict_icon=icon,
        risk_score=int(incident.final_score),
        caller_type=incident.caller_type,
        primary_reason=incident.decision_reason,
        indicators=incident.reason_codes[:5],
        transcript_excerpt=incident.transcript_text[:200] + ("..." if len(incident.transcript_text) > 200 else ""),
        scam_phrases=incident.scam_phrases[:5],
        caller_number=incident.scammer_number,
        victim_number=incident.victim_number,
        call_duration=duration_str,
        evidence_hash=incident.incident_hash[:16],
        chain_verified=True,
        action_taken=action,
        user_instruction=instruction
    )


def print_judge_summary(summary: JudgeSummary):
    """Pretty print judge summary for demo."""
    
    print("\n" + "="*70)
    print(f"{summary.verdict_icon} INCIDENT SUMMARY - {summary.incident_id}")
    print("="*70)
    
    print(f"\n📞 CALL INFORMATION:")
    print(f"   From: {summary.caller_number}")
    print(f"   To: {summary.victim_number}")
    print(f"   Duration: {summary.call_duration}")
    print(f"   Time: {summary.timestamp}")
    
    print(f"\n🎯 VERDICT: {summary.verdict_icon} {summary.verdict} (Score: {summary.risk_score}/100)")
    print(f"   Caller Type: {summary.caller_type}")
    print(f"   Primary Reason: {summary.primary_reason}")
    
    print(f"\n🔍 INDICATORS FOUND:")
    for indicator in summary.indicators:
        print(f"   • {indicator}")
    
    print(f"\n📝 TRANSCRIPT EXCERPT:")
    print(f"   \"{summary.transcript_excerpt}\"")
    
    if summary.scam_phrases:
        print(f"\n⚠️ SCAM PHRASES DETECTED:")
        for phrase in summary.scam_phrases:
            print(f"   • \"{phrase}\"")
    
    print(f"\n🔒 FORENSIC EVIDENCE:")
    print(f"   Evidence Hash: {summary.evidence_hash}")
    print(f"   Chain Verified: {'✅ YES' if summary.chain_verified else '❌ NO'}")
    
    print(f"\n✅ ACTION TAKEN: {summary.action_taken}")
    print(f"   {summary.user_instruction}")
    
    print("\n" + "="*70 + "\n")


# Alias for backward compatibility
create_judge_summary = create_judge_summary
print_judge_summary = print_judge_summary


# Quick test
if __name__ == "__main__":
    from incident_state import UnifiedIncidentState
    
    print("\n" + "="*50)
    print("Testing Judge Summary")
    print("="*50)
    
    # Create test incident
    test_incident = UnifiedIncidentState(
        incident_id="test_001",
        call_id="call_123",
        scammer_number="+15551234567",
        victim_number="+919876543210",
        caller_type="ai-likely",
        transcript_text="Your account is compromised. Share OTP immediately.",
        final_risk="DANGEROUS",
        final_score=95.5,
        decision_reason="OTP request detected",
        reason_codes=["otp_request", "urgent_action"],
        scam_phrases=["OTP", "account blocked"]
    )
    
    # Create summary
    summary = create_judge_summary(test_incident, 45.5)
    print_judge_summary(summary)
    
    print("✅ Judge summary test passed!")
