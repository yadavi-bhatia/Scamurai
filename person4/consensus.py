from state import CallState

def risk_label(final_score: int) -> str:
    if final_score <= 29:
        return "SAFE"
    elif final_score <= 69:
        return "SUSPICIOUS"
    return "DANGEROUS"


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
    final_risk = risk_label(final_score)

    if caller_type == "AI-likely" and scam_likelihood < 35:
        final_risk = "SUSPICIOUS"
        decision_reason = "AI-likely voice signal but low transcript risk, marked cautious instead of dangerous."
    elif caller_type == "human-likely" and scam_likelihood >= 85:
        final_risk = "DANGEROUS"
        final_score = max(final_score, scam_likelihood)
        decision_reason = "Transcript strongly indicates scam behavior, so transcript signal overrides human-likely voice."
    elif caller_type == "AI-likely" and scam_likelihood >= 70:
        final_risk = "DANGEROUS"
        final_score = max(final_score, 85)
        decision_reason = "Both transcript and voice signals are suspicious, so risk is escalated strongly."
    else:
        decision_reason = (
            f"Combined transcript risk ({scam_likelihood}) with voice-derived risk ({voice_risk}); "
            f"transcript_weight={transcript_weight:.2f}, voice_weight={voice_weight:.2f}."
        )

    decision_notes = (
        f"scam_type={scam_type}; reasons={reason_codes}; "
        f"transcript_weight={transcript_weight:.2f}; voice_weight={voice_weight:.2f}; "
        f"signal_quality={signal_quality:.2f}; caller_type={caller_type}"
    )

    return {
        "final_score": final_score,
        "final_risk": final_risk,
        "decision_reason": decision_reason,
        "decision_notes": decision_notes
    }