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

    # =========================
    # SIGNAL EXTRACTION
    # =========================

    ling = analyze_text(transcript,audio_bytes)

    # ✅ FIX: normalize linguistic (0–100 → 0–1)
    ling_score = ling.get("scam_likelihood", 0)
    ling_score = ling_score / 100 if ling_score > 1 else ling_score

    imp = detect_impersonation(transcript)
    imp = imp / 100 if isinstance(imp, (int, float)) and imp > 1 else imp

    money = analyze_money_risk(transcript)
    money = money / 100 if isinstance(money, (int, float)) and money > 1 else money

    deep = detect_deepfake(audio_bytes)
    deep = deep / 100 if isinstance(deep, (int, float)) and deep > 1 else deep

    voice = analyze_voice(audio_bytes)

    # =========================
    # SIGNALS COMBINED
    # =========================

    signals = {
        "linguistic_score": ling_score,
        "impersonation_score": imp,
        "money_risk": money,
        "voice_risk": voice.get("deepfake_risk_score", 0),
        "confidence": voice.get("confidence_score", 0.5)
    }

    # =========================
    # FINAL DECISION
    # =========================

    decision = get_final_decision(signals)

    # =========================
    # ALERT GENERATION
    # =========================

    alerts = []

    if signals["linguistic_score"] > 0.7:
        alerts.append("Suspicious language detected")

    if signals["money_risk"] > 0.7:
        alerts.append("Financial risk indicators detected")

    if signals["impersonation_score"] > 0.7:
        alerts.append("Possible impersonation detected")

    if signals["voice_risk"] > 0.7:
        alerts.append("Voice inconsistency detected")

    # =========================
    # LOGGING
    # =========================

    trigger_alert(decision)

    log_event({
        "signals": signals,
        "decision": decision,
        "transcript": transcript
    })

    # =========================
    # FINAL OUTPUT
    # =========================

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


# =========================
# TEST RUNNER
# =========================

if __name__ == "__main__":

    test_files = [
        ("Audio 1", "audio1.wav"),
        ("Audio 2", "audio2.wav"),
    ]

    for name, file in test_files:
        print("\n" + "=" * 50)
        print(f"📞 Testing: {name}")
        print("=" * 50)

        try:
            with open(file, "rb") as f:
                audio_bytes = f.read()

            result = run_pipeline(audio_bytes)

            print("\n📝 Transcript:")
            print(result["transcript"])

            print("\n⚠️ Risk Level:")
            print(result["decision"]["risk_level"])

            print("\n📊 Signals:")
            for k, v in result["signals"].items():
                print(f"{k}: {round(v, 2)}")

            print("\n🚨 Alerts:")
            for alert in result["alerts"]:
                print("-", alert)

        except Exception as e:
            print("❌ Error:", e)