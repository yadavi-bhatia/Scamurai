# app/main.py

import time

from app.utils.adapters import (
    analyze_text,
    detect_impersonation,
    analyze_money_risk,
    detect_deepfake,
    get_final_decision,
    trigger_alert,
    log_event
)

from app.voice.analyzer import analyze_voice
from app.audio.transcriber import transcribe_audio


def run_pipeline(audio_bytes):

    start_time = time.time()

    transcript = transcribe_audio(audio_bytes)

    ling = analyze_text(transcript)
    imp = detect_impersonation(transcript)
    money = analyze_money_risk(transcript)
    deep = detect_deepfake(audio_bytes)

    voice = analyze_voice(audio_bytes)

    signals = {
        "linguistic_score": ling.get("scam_likelihood", 0),
        "impersonation_score": imp,
        "money_risk": money,
        "voice_risk": voice.get("deepfake_risk_score", 0),
        "confidence": voice.get("confidence_score", 0.5)
    }

    decision = get_final_decision(signals)

    # 🔥 Generate simple explainability alerts
    alerts = []

    if signals["linguistic_score"] > 0.7:
        alerts.append("Suspicious language detected")

    if signals["money_risk"] > 0.7:
        alerts.append("Financial risk indicators detected")

    if signals["impersonation_score"] > 0.7:
        alerts.append("Possible impersonation detected")

    if signals["voice_risk"] > 0.7:
        alerts.append("Voice inconsistency detected")

    # 🔔 Trigger + log (unchanged)
    trigger_alert(decision)

    log_event({
        "signals": signals,
        "decision": decision,
        "transcript": transcript
    })

    # ✅ FINAL STRUCTURED RESPONSE (frontend-ready)
    result = {
        "call_id": "demo_call",
        "timestamp": time.time(),
        "processing_time_ms": int((time.time() - start_time) * 1000),

        "transcript": transcript,

        "signals": signals,

        "decision": decision,

        "alerts": alerts,

        "status": "COMPLETED"
    }

    return result


if __name__ == "__main__":
    fake_audio = b"\x00\x01" * 8000
    result = run_pipeline(fake_audio)
    print(result)