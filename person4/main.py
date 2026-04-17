from graph import graph
from audit_log import verify_chain

sample_input = {
    "call_id": "call_001",
    "stream_sid": "stream_001",
    "timestamp": "2026-04-17T17:30:00",
    "caller_number": "+911234567890",
    "transcript": "Your bank account is blocked. Tell me the OTP now.",
    "voice_score": 0.82,
    "signal_quality": 0.71,
    "caller_type": "AI-likely",
    "scam_likelihood": 91,
    "scam_type": "bank impersonation",
    "reason_codes": ["urgency", "OTP request", "authority impersonation"]
}

result = graph.invoke(sample_input)

for key, value in result.items():
    print(f"{key}: {value}")

print("\nChain verification:")
verification = verify_chain()
for key, value in verification.items():
    print(f"{key}: {value}")

if result.get("alert_mode") == "RED_ALERT":
    print("\n=== RED ALERT ===")
    print(result.get("user_message"))
    print("Caller type:", result.get("caller_type"))
    print("Reasons:", result.get("reason_codes"))
    print("Action:", result.get("action"))
    print("Evidence:", result.get("evidence_summary"))
    if result.get("hold_message"):
        print("Hold message:", result.get("hold_message"))