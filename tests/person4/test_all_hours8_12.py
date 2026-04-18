"""Test all Hours 8-12 components together."""

from datetime import datetime
from incident_state import UnifiedIncidentState, IncidentManager
from dashboard import create_dashboard
from consensus_framework import ConsensusFramework
from evidence_chain import EvidenceChain
from judge_summary import create_judge_summary, print_judge_summary

print("\n" + "="*70)
print("TESTING ALL HOURS 8-12 COMPONENTS")
print("="*70)

# 1. Test Consensus Framework
print("\n📊 1. Consensus Framework")
cf = ConsensusFramework()
result = cf.combine(95, 85, 0.8, {"otp_request": True})
print(f"   Result: {result['final_risk']} (Score: {result['final_score']})")

# 2. Test Evidence Chain
print("\n🔗 2. Evidence Chain")
chain = EvidenceChain("data/test_chain.jsonl")
block = chain.append({
    "call_id": "test_001",
    "risk": result['final_risk'],
    "score": result['final_score']
})
print(f"   Block added at index: {block.index}")
print(f"   Block hash: {block.hash[:16]}...")

# 3. Verify chain
verification = chain.verify()
print(f"   Chain valid: {verification['valid']}")

# 4. Create Unified Incident
print("\n📋 3. Unified Incident State")
incident = UnifiedIncidentState(
    incident_id="test_integration_001",
    call_id="exotel_12345",
    scammer_number="+15551234567",
    victim_number="+919876543210",
    caller_type="ai-likely",
    transcript_text="Your account is compromised. Share OTP immediately.",
    final_risk=result['final_risk'],
    final_score=result['final_score'],
    decision_reason=result['reason'],
    reason_codes=["otp_request", "urgent_action"],
    scam_phrases=["OTP", "compromised"],
    overall_confidence=result['confidence'],
    recommended_action="block",
    incident_hash=block.hash[:16],
    chain_position=block.index,
    start_time=datetime.now(),
    processing_time_ms=234
)
print(f"   Incident created: {incident.incident_id}")
print(f"   Risk: {incident.final_risk}")

# 5. Create Dashboard Output
print("\n📺 4. Dashboard Contract")
dashboard = create_dashboard(incident)
print(f"   Risk Level: {dashboard.risk_level.value}")
print(f"   Risk Score: {dashboard.risk_score}")
print(f"   Confidence: {dashboard.confidence_percentage}%")
print(f"   Action: {dashboard.recommended_action}")

# 6. Create Judge Summary
print("\n👨‍⚖️ 5. Judge Summary")
summary = create_judge_summary(incident, 45.0)
print(f"   Verdict: {summary.verdict}")
print(f"   Verdict Icon: {summary.verdict_icon}")
print(f"   Primary Reason: {summary.primary_reason}")
print(f"   Action Taken: {summary.action_taken}")

print("\n" + "="*70)
print("✅ ALL HOURS 8-12 COMPONENTS WORKING!")
print("="*70 + "\n")
