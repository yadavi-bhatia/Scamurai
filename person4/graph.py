from langgraph.graph import StateGraph, START, END
from state import CallState
from consensus import consensus_node
from audit_log import log_node

def voice_node(state: CallState):
    return {}

def transcript_node(state: CallState):
    return {}

def response_node(state: CallState):
    final_risk = state.get("final_risk", "SAFE")
    caller_type = state.get("caller_type", "uncertain")
    reasons = state.get("reason_codes", [])
    transcript = state.get("transcript", "")
    final_score = state.get("final_score", 0)
    timestamp = state.get("timestamp", "")

    if final_risk == "DANGEROUS":
        action = "warn_and_delay"
        alert_mode = "RED_ALERT"
        user_message = "Dangerous call detected. Do not share OTP, PIN, or bank details."
        hold_message = "Please wait while we verify this caller."
    elif final_risk == "SUSPICIOUS":
        action = "warn_user"
        alert_mode = "AMBER_ALERT"
        user_message = "Suspicious call detected. Verify the caller before sharing any information."
        hold_message = "Please hold while this call is checked."
    else:
        action = "allow"
        alert_mode = "NONE"
        user_message = "No major risk detected."
        hold_message = ""

    excerpt = transcript[:120] + ("..." if len(transcript) > 120 else "")
    evidence_summary = (
        f"Risk={final_risk}; score={final_score}; caller_type={caller_type}; "
        f"reasons={reasons}; transcript_excerpt='{excerpt}'; timestamp={timestamp}"
    )

    return {
        "action": action,
        "alert_mode": alert_mode,
        "user_message": user_message,
        "hold_message": hold_message,
        "evidence_summary": evidence_summary,
        "event_type": "call_risk_assessment",
        "source_system": "person4_consensus_agent",
        "outcome": "logged"
    }

builder = StateGraph(CallState)

builder.add_node("voice_node", voice_node)
builder.add_node("transcript_node", transcript_node)
builder.add_node("consensus_node", consensus_node)
builder.add_node("response_node", response_node)
builder.add_node("log_node", log_node)

builder.add_edge(START, "voice_node")
builder.add_edge(START, "transcript_node")
builder.add_edge("voice_node", "consensus_node")
builder.add_edge("transcript_node", "consensus_node")
builder.add_edge("consensus_node", "response_node")
builder.add_edge("response_node", "log_node")
builder.add_edge("log_node", END)

graph = builder.compile()