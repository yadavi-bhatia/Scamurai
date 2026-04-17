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
    decision_notes: str

    prev_hash: str
    hash: str