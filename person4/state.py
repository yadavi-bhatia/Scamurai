from typing import List
from typing_extensions import TypedDict

class CallState(TypedDict, total=False):
    call_id: str
    stream_sid: str
    timestamp: str
    caller_number: str

    transcript: str
    transcript_chunks: List[str]

    voice_score: float
    signal_quality: float
    caller_type: str

    scam_likelihood: int
    scam_type: str
    reason_codes: List[str]

    final_score: int
    final_risk: str
    decision_reason: str
    decision_notes: str

    action: str
    alert_mode: str
    user_message: str
    hold_message: str
    evidence_summary: str

    source_system: str
    event_type: str
    outcome: str

    prev_hash: str
    hash: str