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
print(result)
print(verify_chain())