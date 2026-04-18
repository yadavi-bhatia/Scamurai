from services.linguistic import linguistic_agent
from services.detectors import impersonation_detector, money_risk_analyzer, deepfake_detector
from engine import consensus_engine, alert_actions
from engine.evidence import evidence_chain


def analyze_text(text):
    if hasattr(linguistic_agent, "analyze"):
        return linguistic_agent.analyze(text)
    if hasattr(linguistic_agent, "run"):
        return linguistic_agent.run(text)
    return {"scam_likelihood": 0.5}


def detect_impersonation(text):
    if hasattr(impersonation_detector, "detect"):
        return impersonation_detector.detect(text)
    return 0.5


def analyze_money_risk(text):
    if hasattr(money_risk_analyzer, "analyze"):
        return money_risk_analyzer.analyze(text)
    return 0.5


def detect_deepfake(audio):
    if hasattr(deepfake_detector, "detect"):
        return deepfake_detector.detect(audio)
    return 0.5


def get_final_decision(signals):
    if hasattr(consensus_engine, "get_final_decision"):
        return consensus_engine.get_final_decision(signals)
    if hasattr(consensus_engine, "decide"):
        return consensus_engine.decide(signals)
    return {"risk_score": 0.5, "risk_level": "LOW"}


def trigger_alert(decision):
    if hasattr(alert_actions, "trigger_alert"):
        return alert_actions.trigger_alert(decision)
    print("ALERT:", decision)


def log_event(data):
    if hasattr(evidence_chain, "log_event"):
        return evidence_chain.log_event(data)
    print("LOG:", data)