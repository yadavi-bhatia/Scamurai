from services.linguistic import linguistic_agent
from services.detectors import impersonation_detector, deepfake_detector
from services.detectors.money_risk_analyzer import money_risk_analyzer
from engine import consensus_engine, alert_actions
from engine.evidence import evidence_chain


def analyze_text(text, audio_bytes=None):
    return linguistic_agent.analyze_transcript(text, audio_bytes=audio_bytes)


def detect_impersonation(text):
    return impersonation_detector.detect(text) if hasattr(impersonation_detector, "detect") else 0.0


def analyze_money_risk(text):
    return money_risk_analyzer.analyze(text)


def detect_deepfake(audio):
    return deepfake_detector.detect(audio) if hasattr(deepfake_detector, "detect") else 0.0


def get_final_decision(signals):
    if hasattr(consensus_engine, "get_final_decision"):
        return consensus_engine.get_final_decision(signals)
    return consensus_engine.decide(signals)


def trigger_alert(decision):
    if hasattr(alert_actions, "trigger_alert"):
        return alert_actions.trigger_alert(decision)
    print("ALERT:", decision)


def log_event(data):
    if hasattr(evidence_chain, "log_event"):
        return evidence_chain.log_event(data)
    print("LOG:", data)