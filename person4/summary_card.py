
"""Hour 15: Summary Card - Readable demo summary structure."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class SummaryCard(BaseModel):
    """Readable, demo-friendly summary card."""
    incident_id: str
    timestamp: str
    verdict: str
    verdict_icon: str
    risk_score: int
    caller_number: str
    victim_number: str
    call_duration: str
    caller_type: str
    primary_reason: str
    indicators: List[str]
    transcript_excerpt: str
    scam_phrases: List[str]
    evidence_hash: str
    chain_position: int
    chain_verified: bool
    action_taken: str
    user_instruction: str


def create_summary_card(
    call_id: str,
    verdict: str,
    risk_score: float,
    caller_type: str,
    reason: str,
    indicators: List[str],
    transcript: str,
    scam_phrases: List[str],
    caller_number: str,
    victim_number: str,
    incident_hash: str,
    chain_position: int,
    duration_seconds: float = 0
) -> SummaryCard:
    if verdict == "DANGEROUS":
        icon = "🔴"
        action = "BLOCKED + Hold Music"
        instruction = "⚠️ NEVER share OTP, PIN, or passwords!"
    elif verdict == "SUSPICIOUS":
        icon = "🟡"
        action = "WARNING Displayed"
        instruction = "⚠️ Verify caller identity"
    else:
        icon = "🟢"
        action = "ALLOWED"
        instruction = "ℹ️ Call appears safe"
    
    mins = int(duration_seconds // 60)
    secs = int(duration_seconds % 60)
    duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
    
    return SummaryCard(
        incident_id=f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        verdict=verdict,
        verdict_icon=icon,
        risk_score=int(risk_score),
        caller_number=caller_number,
        victim_number=victim_number,
        call_duration=duration_str,
        caller_type=caller_type,
        primary_reason=reason,
        indicators=indicators[:5],
        transcript_excerpt=transcript[:200] + ("..." if len(transcript) > 200 else ""),
        scam_phrases=scam_phrases[:5],
        evidence_hash=incident_hash[:16],
        chain_position=chain_position,
        chain_verified=True,
        action_taken=action,
        user_instruction=instruction
    )


def print_summary_card(card: SummaryCard):
    print("\n" + "="*70)
    print(f"{card.verdict_icon} INCIDENT SUMMARY")
    print("="*70)
    print(f"\n📋 Incident: {card.incident_id}")
    print(f"🎯 Verdict: {card.verdict_icon} {card.verdict} (Score: {card.risk_score}/100)")
    print(f"📞 From: {card.caller_number} → To: {card.victim_number}")
    print(f"🔍 Reason: {card.primary_reason}")
    print(f"🔒 Hash: {card.evidence_hash}")
    print(f"✅ Action: {card.action_taken}")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("✅ Hour 15: summary_card.py ready")
