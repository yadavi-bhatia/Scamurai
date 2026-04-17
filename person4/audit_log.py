import json
import hashlib
from pathlib import Path
from state import CallState

LOG_FILE = Path("incident_log.jsonl")
GENESIS_HASH = "GENESIS"

def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"))

def compute_hash(payload, prev_hash):
    raw = canonical_json({
        "prev_hash": prev_hash,
        "payload": payload
    }).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def get_last_hash():
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        return GENESIS_HASH
    last_line = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()[-1]
    return json.loads(last_line)["hash"]

def log_node(state: CallState):
    prev_hash = get_last_hash()

    payload = {
        "event_type": state.get("event_type", "call_risk_assessment"),
        "source_system": state.get("source_system", "person4_consensus_agent"),
        "outcome": state.get("outcome", "logged"),
        "call_id": state.get("call_id"),
        "stream_sid": state.get("stream_sid"),
        "timestamp": state.get("timestamp"),
        "caller_number": state.get("caller_number"),
        "caller_type": state.get("caller_type"),
        "voice_score": state.get("voice_score"),
        "signal_quality": state.get("signal_quality"),
        "transcript": state.get("transcript"),
        "scam_likelihood": state.get("scam_likelihood"),
        "scam_type": state.get("scam_type"),
        "reason_codes": state.get("reason_codes", []),
        "final_score": state.get("final_score"),
        "final_risk": state.get("final_risk"),
        "decision_reason": state.get("decision_reason"),
        "decision_notes": state.get("decision_notes"),
        "action": state.get("action"),
        "alert_mode": state.get("alert_mode"),
        "user_message": state.get("user_message"),
        "hold_message": state.get("hold_message"),
        "evidence_summary": state.get("evidence_summary")
    }

    event_hash = compute_hash(payload, prev_hash)

    record = {
        "prev_hash": prev_hash,
        "hash": event_hash,
        "payload": payload
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {
        "prev_hash": prev_hash,
        "hash": event_hash
    }

def verify_chain():
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        return {"valid": True, "count": 0}

    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    prev = GENESIS_HASH

    for i, line in enumerate(lines):
        record = json.loads(line)

        if record["prev_hash"] != prev:
            return {"valid": False, "index": i, "reason": "prev_hash mismatch"}

        expected_hash = compute_hash(record["payload"], record["prev_hash"])
        if record["hash"] != expected_hash:
            return {"valid": False, "index": i, "reason": "event_hash mismatch"}

        prev = record["hash"]

    return {"valid": True, "count": len(lines)}