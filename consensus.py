from state import CallState

def consensus_node(state: CallState):
    voice_score = float(state.get("voice_score", 0.0))
    signal_quality = float(state.get("signal_quality", 0.0))
    caller_type = state.get("caller_type", "uncertain")

    scam_likelihood = int(state.get("scam_likelihood", 0))
    scam_type = state.get("scam_type", "unknown")
    reason_codes = state.get("reason_codes", [])

    if caller_type == "AI-likely":
        voice_risk = int(voice_score * 100)
    elif caller_type == "uncertain":
        voice_risk = int(voice_score * 60)
    else:
        voice_risk = int((1 - voice_score) * 20)

    voice_weight = 0.15 if signal_quality < 0.4 else 0.30
    transcript_weight = 1.0 - voice_weight

    final_score = round((scam_likelihood * transcript_weight) + (voice_risk * voice_weight))

    if scam_likelihood >= 85 or final_score >= 70:
        final_risk = "DANGEROUS"
    elif final_score >= 30:
        final_risk = "SUSPICIOUS"
    else:
        final_risk = "SAFE"

    return {
        "final_score": final_score,
        "final_risk": final_risk,
        "decision_notes": f"scam_type={scam_type}; reasons={reason_codes}; transcript_weight={transcript_weight:.2f}; voice_weight={voice_weight:.2f}"
    }