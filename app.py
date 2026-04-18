import os
import json
import base64
import wave
import tempfile
import threading
import time
from datetime import datetime, timezone
from collections import deque

import requests
import numpy as np
import librosa

from flask import Flask, request, jsonify
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

PERSON2_URL = os.environ.get("PERSON2_URL")
PERSON3_URL = os.environ.get("PERSON3_URL")
PERSON4_URL = os.environ.get("PERSON4_URL")
FORWARD_TIMEOUT = float(os.environ.get("FORWARD_TIMEOUT", "5"))

AUDIO_FORMAT = "raw/slin;rate=8000;channels=1;sample_width=16le"
DEBUG_BUFFER_LIMIT_BYTES = 32000
LATEST_QUEUE_MAXLEN = 200
DEBUG_AUDIO_DIR = os.environ.get("DEBUG_AUDIO_DIR", "debug_audio")
SCHEMA_VERSION = "1.0"
VOICE_SCHEMA_VERSION = "1.0"

DATA_DIR = os.environ.get("DATA_DIR", "data")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")
LATEST_CHUNK_FILE = os.path.join(DATA_DIR, "latest_chunk.json")
QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")
ANALYSIS_QUEUE_FILE = os.path.join(DATA_DIR, "voice_analysis_queue.json")
LATEST_ANALYSIS_FILE = os.path.join(DATA_DIR, "latest_voice_analysis.json")

REFERENCE_VOICE_FILE = os.environ.get("REFERENCE_VOICE_FILE", "reference_voice.wav")
VOICE_ANALYSIS_DIR = os.environ.get("VOICE_ANALYSIS_DIR", "voice_analysis")
MIN_SEGMENT_MS = int(os.environ.get("MIN_SEGMENT_MS", "1000"))
MAX_SEGMENT_MS = int(os.environ.get("MAX_SEGMENT_MS", "2000"))
MIN_AUDIO_BYTES_FOR_ANALYSIS = int(os.environ.get("MIN_AUDIO_BYTES_FOR_ANALYSIS", "16000"))
VAD_SILENCE_MS = int(os.environ.get("VAD_SILENCE_MS", "400"))
PERSON2_RECEIVER_NUMBER = os.environ.get("PERSON2_RECEIVER_NUMBER", "+91 8147512878")

os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VOICE_ANALYSIS_DIR, exist_ok=True)

sessions = {}
latest_chunk = None
handoff_queue = deque(maxlen=LATEST_QUEUE_MAXLEN)
debug_buffers = {}
analysis_buffers = {}
voice_analysis_queue = deque(maxlen=LATEST_QUEUE_MAXLEN)
latest_voice_analysis = None
segment_buffers = {}
segment_states = {}

# Global cache for reference MFCC voiceprint
_reference_mfcc_voiceprint = None


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def unix_now():
    return time.time()


def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def short_log(payload):
    print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), flush=True)


def normalize_phone(value):
    if value is None:
        return None
    return str(value).strip()


def pcm16le_bytes_to_float32(audio_bytes):
    if not audio_bytes:
        return np.array([], dtype=np.float32)
    pcm = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    if pcm.size == 0:
        return np.array([], dtype=np.float32)
    return pcm / 32768.0


def write_wav_file(path, audio_bytes, sample_rate=8000):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)


def rms_energy(signal):
    if signal.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(signal))))


def zero_crossing_rate(signal):
    if signal.size < 2:
        return 0.0
    return float(np.mean(np.abs(np.diff(np.signbit(signal)).astype(np.int8))))


def estimate_noise_floor(signal):
    if signal.size == 0:
        return 0.0
    frame = max(80, min(400, signal.size // 20 or 80))
    energies = []
    for i in range(0, len(signal), frame):
        chunk = signal[i:i + frame]
        if chunk.size:
            energies.append(np.sqrt(np.mean(np.square(chunk))))
    if not energies:
        return 0.0
    energies = np.array(energies, dtype=np.float32)
    return float(np.percentile(energies, 20))


def estimate_snr_db(signal):
    if signal.size == 0:
        return 0.0
    signal_rms = rms_energy(signal)
    noise_rms = max(estimate_noise_floor(signal), 1e-6)
    if signal_rms <= 0:
        return 0.0
    snr = 20.0 * np.log10(max(signal_rms, 1e-6) / noise_rms)
    return float(max(min(snr, 60.0), -20.0))


def get_quality_label(score):
    if score >= 0.8:
        return "good"
    if score >= 0.55:
        return "fair"
    return "poor"


def compute_signal_quality(signal, duration_sec):
    if signal.size == 0 or duration_sec <= 0:
        return {
            "quality_score": 0.0,
            "quality_label": "poor",
            "snr_db": 0.0,
            "rms": 0.0,
            "zero_crossing_rate": 0.0,
            "duration_sec": duration_sec,
            "notes": ["empty_audio"]
        }

    rms = rms_energy(signal)
    zcr = zero_crossing_rate(signal)
    snr_db = estimate_snr_db(signal)
    duration_score = min(duration_sec / 3.0, 1.0)
    snr_score = min(max((snr_db + 5.0) / 25.0, 0.0), 1.0)
    rms_score = min(max((rms - 0.005) / 0.06, 0.0), 1.0)
    zcr_penalty = 1.0 - min(max((zcr - 0.25) / 0.35, 0.0), 1.0)
    quality_score = float(max(min(0.35 * duration_score + 0.35 * snr_score + 0.2 * rms_score + 0.1 * zcr_penalty, 1.0), 0.0))
    notes = []
    if duration_sec < 1.0:
        notes.append("very_short_audio")
    elif duration_sec < 2.0:
        notes.append("short_audio")
    if snr_db < 8:
        notes.append("noisy_audio")
    if rms < 0.01:
        notes.append("low_volume")
    if zcr > 0.32:
        notes.append("possible_noise_or_clipping")
    return {
        "quality_score": quality_score,
        "quality_label": get_quality_label(quality_score),
        "snr_db": round(snr_db, 3),
        "rms": round(rms, 6),
        "zero_crossing_rate": round(zcr, 6),
        "duration_sec": round(duration_sec, 3),
        "notes": notes
    }


def extract_mfcc_voiceprint(audio_bytes, sample_rate=8000):
    """
    Extract a voiceprint from audio bytes using MFCC features.
    Returns a 39-dimensional vector (13 MFCC + delta + delta-delta) averaged over time.
    """
    signal = pcm16le_bytes_to_float32(audio_bytes)
    if signal.size == 0:
        return None

    # Compute MFCC (13 coefficients)
    mfcc = librosa.feature.mfcc(y=signal, sr=sample_rate, n_mfcc=13)

    # Compute delta (first derivative)
    mfcc_delta = librosa.feature.delta(mfcc)

    # Compute delta-delta (second derivative)
    mfcc_delta2 = librosa.feature.delta(mfcc, order=2)

    # Stack and average over time to get a single vector
    features = np.vstack([mfcc, mfcc_delta, mfcc_delta2])  # shape: (39, time_frames)
    voiceprint = np.mean(features, axis=1)  # shape: (39,)

    # Normalize to unit length for cosine similarity
    norm = np.linalg.norm(voiceprint)
    if norm > 0:
        voiceprint = voiceprint / norm

    return voiceprint


def load_reference_mfcc_voiceprint():
    global _reference_mfcc_voiceprint
    if _reference_mfcc_voiceprint is not None:
        return _reference_mfcc_voiceprint

    if not os.path.exists(REFERENCE_VOICE_FILE):
        return None

    try:
        with open(REFERENCE_VOICE_FILE, 'rb') as f:
            ref_bytes = f.read()
        _reference_mfcc_voiceprint = extract_mfcc_voiceprint(ref_bytes)
        return _reference_mfcc_voiceprint
    except Exception:
        return None


def cosine_similarity(vec_a, vec_b):
    if vec_a is None or vec_b is None:
        return None
    # Vectors are already normalized, so dot product equals cosine similarity
    return float(np.dot(vec_a, vec_b))


def simple_extract_voice_segment(audio_bytes, sample_rate=8000):
    signal = pcm16le_bytes_to_float32(audio_bytes)
    if signal.size == 0:
        return b"", {"method": "energy_gate", "speech_detected": False, "start_sample": 0, "end_sample": 0, "duration_sec": 0.0}
    abs_signal = np.abs(signal)
    threshold = max(np.percentile(abs_signal, 65) * 0.6, 0.01)
    voiced = np.where(abs_signal >= threshold)[0]
    if voiced.size == 0:
        return b"", {"method": "energy_gate", "speech_detected": False, "start_sample": 0, "end_sample": 0, "duration_sec": 0.0}
    start = int(voiced[0])
    end = int(voiced[-1]) + 1
    pad = int(sample_rate * 0.15)
    start = max(0, start - pad)
    end = min(len(signal), end + pad)
    extracted = signal[start:end]
    extracted_bytes = (np.clip(extracted, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
    return extracted_bytes, {"method": "energy_gate", "speech_detected": True, "start_sample": start, "end_sample": end, "duration_sec": round((end - start) / float(sample_rate), 3)}


def embed_audio_bytes(audio_bytes, sample_rate=8000):
    """Compute MFCC voiceprint for audio bytes."""
    try:
        voiceprint = extract_mfcc_voiceprint(audio_bytes, sample_rate)
        if voiceprint is None:
            return None, "mfcc_extraction_failed"
        return voiceprint, None
    except Exception as e:
        return None, str(e)


def analyze_voice(audio_bytes, stream_sid=None, call_id=None, caller_number=None, sample_rate=8000):
    if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES_FOR_ANALYSIS:
        return {
            "schema_version": VOICE_SCHEMA_VERSION,
            "stream_sid": stream_sid,
            "call_id": call_id,
            "caller_number": caller_number,
            "status": "fallback",
            "label": "insufficient_audio",
            "similarity_score": None,
            "confidence_score": 0.0,
            "signal_quality_score": 0.0,
            "signal_quality_label": "poor",
            "reference_available": os.path.exists(REFERENCE_VOICE_FILE),
            "notes": ["not_enough_audio_for_analysis"],
            "received_at": iso_now()
        }

    segment_bytes, segment_meta = simple_extract_voice_segment(audio_bytes, sample_rate=sample_rate)
    if not segment_bytes:
        return {
            "schema_version": VOICE_SCHEMA_VERSION,
            "stream_sid": stream_sid,
            "call_id": call_id,
            "caller_number": caller_number,
            "status": "fallback",
            "label": "uncertain",
            "similarity_score": None,
            "confidence_score": 0.0,
            "signal_quality_score": 0.0,
            "signal_quality_label": "poor",
            "reference_available": os.path.exists(REFERENCE_VOICE_FILE),
            "notes": ["speech_not_detected"],
            "segment": segment_meta,
            "received_at": iso_now()
        }

    segment_signal = pcm16le_bytes_to_float32(segment_bytes)
    duration_sec = len(segment_signal) / float(sample_rate)
    quality = compute_signal_quality(segment_signal, duration_sec)
    incoming_voiceprint, incoming_error = embed_audio_bytes(segment_bytes, sample_rate=sample_rate)
    reference_voiceprint = load_reference_mfcc_voiceprint()
    notes = list(quality.get("notes", []))
    if incoming_error:
        notes.append(f"embedding_error:{incoming_error}")
    if reference_voiceprint is None:
        if not os.path.exists(REFERENCE_VOICE_FILE):
            notes.append("reference_voice_missing")
        else:
            notes.append("reference_embedding_error:mfcc_extraction_failed")
    similarity = cosine_similarity(reference_voiceprint, incoming_voiceprint) if incoming_voiceprint is not None and reference_voiceprint is not None else None
    if similarity is None:
        confidence = max(quality["quality_score"] * 0.5, 0.0)
    else:
        margin = abs(similarity - 0.68)
        confidence = max(min(0.55 * quality["quality_score"] + 0.45 * min(margin / 0.22, 1.0), 1.0), 0.0)
    label = "uncertain"
    if similarity is not None and confidence >= 0.45:
        if similarity >= 0.78:
            label = "same_voice"
        elif similarity <= 0.58:
            label = "different_voice"
    if quality["quality_score"] < 0.35:
        label = "uncertain"
        notes.append("quality_too_low")
    result = {
        "schema_version": VOICE_SCHEMA_VERSION,
        "stream_sid": stream_sid,
        "call_id": call_id,
        "caller_number": caller_number,
        "status": "ok" if similarity is not None and reference_voiceprint is not None else "fallback",
        "label": label,
        "similarity_score": round(similarity, 6) if similarity is not None else None,
        "confidence_score": round(confidence, 6),
        "signal_quality_score": round(quality["quality_score"], 6),
        "signal_quality_label": quality["quality_label"],
        "reference_available": reference_voiceprint is not None,
        "segment": segment_meta,
        "duration_sec": quality["duration_sec"],
        "snr_db": quality["snr_db"],
        "rms": quality["rms"],
        "zero_crossing_rate": quality["zero_crossing_rate"],
        "notes": notes,
        "received_at": iso_now()
    }
    return result


def map_voice_analysis_to_agent_schema(voice_result, session, stream_sid, call_id):
    label = voice_result.get("label")
    notes_list = voice_result.get("notes") or []
    confidence = float(voice_result.get("confidence_score") or 0.0)
    signal_quality = float(voice_result.get("signal_quality_score") or 0.0)
    similarity = voice_result.get("similarity_score")
    similarity = float(similarity) if similarity is not None else 0.0
    tone_label = "neutral"
    pace_label = "normal"
    accent_label = "unknown"
    if "low_volume" in notes_list or "very_short_audio" in notes_list:
        tone_label = "unknown"
    if "possible_noise_or_clipping" in notes_list:
        pace_label = "erratic"
    elif voice_result.get("zero_crossing_rate", 0) > 0.22:
        pace_label = "fast"
    elif voice_result.get("zero_crossing_rate", 0) < 0.08:
        pace_label = "slow"
    if label == "same_voice":
        accent_label = "consistent"
    elif label == "different_voice":
        accent_label = "inconsistent"
    urgency_score = max(0.0, min(1.0, 1.0 - signal_quality if tone_label == "unknown" else 0.25))
    deepfake_risk_score = max(0.0, min(1.0, (1.0 - similarity) * 0.7 + (1.0 - confidence) * 0.3)) if voice_result.get("similarity_score") is not None else max(0.0, min(1.0, 1.0 - confidence))
    if deepfake_risk_score >= 0.7:
        final_audio_risk_label = "high"
    elif deepfake_risk_score >= 0.4:
        final_audio_risk_label = "medium"
    else:
        final_audio_risk_label = "low"
    return {
        "call_id": call_id,
        "stream_sid": stream_sid,
        "timestamp": unix_now(),
        "tone_label": tone_label,
        "accent_label": accent_label,
        "pace_label": pace_label,
        "urgency_score": round(urgency_score, 6),
        "voice_match_score": round(similarity, 6),
        "deepfake_risk_score": round(deepfake_risk_score, 6),
        "signal_quality_score": round(signal_quality, 6),
        "confidence_score": round(confidence, 6),
        "notes": ", ".join(notes_list[:6]) if notes_list else "analysis_complete",
        "final_audio_risk_label": final_audio_risk_label,
    }


def save_voice_segment_artifacts(stream_sid, call_id, audio_bytes):
    if not audio_bytes:
        return None, None
    base_name = f"{call_id or 'unknown_call'}_{stream_sid or 'manual'}"
    full_audio_path = os.path.join(VOICE_ANALYSIS_DIR, f"{base_name}_full.wav")
    segment_audio_path = os.path.join(VOICE_ANALYSIS_DIR, f"{base_name}_segment.wav")
    write_wav_file(full_audio_path, audio_bytes, sample_rate=8000)
    segment_bytes, _ = simple_extract_voice_segment(audio_bytes, sample_rate=8000)
    if segment_bytes:
        write_wav_file(segment_audio_path, segment_bytes, sample_rate=8000)
    else:
        segment_audio_path = None
    return full_audio_path, segment_audio_path


def infer_stop_reason(payload):
    candidates = [payload.get("reason"), payload.get("stop_reason"), payload.get("message")]
    stop = payload.get("stop") or {}
    media = payload.get("media") or {}
    start = payload.get("start") or {}
    candidates.extend([stop.get("reason"), stop.get("stop_reason"), media.get("reason"), start.get("reason")])
    for item in candidates:
        if item:
            return str(item)
    return "unknown"


def map_fallback_state(stop_reason, current_state):
    reason = (stop_reason or "").lower()
    if any(x in reason for x in ["no answer", "no_answer", "not answered", "unanswered"]):
        return "no_answer"
    if any(x in reason for x in ["transfer failed", "transfer_failed", "routing failed", "route failed"]):
        return "transfer_failed"
    if any(x in reason for x in ["dropped", "websocket closed unexpectedly", "socket closed", "stream dropped", "network"]):
        return "stream_dropped"
    if current_state in {"started", "connected"}:
        return "call_ended_early"
    return "stopped"


def map_routing_status(call_state, stop_reason=None):
    if call_state == "started":
        return "routing_in_progress"
    if call_state in {"connected", "speaking"}:
        return "transferred_to_phone"
    if call_state == "no_answer":
        return "no_answer"
    if call_state == "transfer_failed":
        return "transfer_failed"
    if call_state == "stream_dropped":
        return "stream_dropped"
    if call_state == "call_ended_early":
        return "call_ended_early"
    if call_state == "stopped":
        return "completed"
    return "unknown"


def get_stream_sid(data):
    return data.get("streamSid") or data.get("stream_sid") or (data.get("start") or {}).get("streamSid") or (data.get("start") or {}).get("stream_sid") or (data.get("media") or {}).get("streamSid") or (data.get("stop") or {}).get("streamSid")


def get_call_id(data):
    start = data.get("start") or {}
    stop = data.get("stop") or {}
    media = data.get("media") or {}
    custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}
    return data.get("callSid") or data.get("CallSid") or data.get("call_id") or data.get("callId") or start.get("callSid") or start.get("CallSid") or start.get("call_id") or start.get("callId") or stop.get("callSid") or stop.get("CallSid") or stop.get("call_id") or stop.get("callId") or media.get("callSid") or media.get("CallSid") or media.get("call_id") or media.get("callId") or custom.get("CallSid") or custom.get("callSid") or custom.get("call_id") or custom.get("callId")


def get_caller_number(data):
    start = data.get("start") or {}
    custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}
    return normalize_phone(data.get("caller_number") or data.get("from") or data.get("From") or start.get("from") or start.get("From") or custom.get("From") or custom.get("CallFrom") or custom.get("caller_number"))


def build_transfer_metadata(existing=None, payload=None, data=None, session=None):
    transfer_metadata = dict(existing or {})
    if "provider" not in transfer_metadata:
        transfer_metadata["provider"] = "exotel"
    if payload:
        transfer_metadata["flow_id"] = payload.get("flow_id") or transfer_metadata.get("flow_id")
        transfer_metadata["direction"] = payload.get("Direction") or transfer_metadata.get("direction")
        transfer_metadata["target_number"] = normalize_phone(payload.get("DialWhomNumber") or payload.get("CallTo") or payload.get("To") or PERSON2_RECEIVER_NUMBER or transfer_metadata.get("target_number"))
        transfer_metadata["from_number"] = normalize_phone(payload.get("CallFrom") or payload.get("From") or transfer_metadata.get("from_number"))
        transfer_metadata["to_number"] = normalize_phone(payload.get("CallTo") or payload.get("To") or PERSON2_RECEIVER_NUMBER or transfer_metadata.get("to_number"))
        transfer_metadata["call_type"] = payload.get("CallType") or transfer_metadata.get("call_type")
        transfer_metadata["tenant_id"] = payload.get("tenant_id") or transfer_metadata.get("tenant_id")
        transfer_metadata["stream_sid"] = payload.get("Stream[StreamSID]") or transfer_metadata.get("stream_sid")
    if data:
        start = data.get("start") or {}
        custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}
        transfer_metadata["flow_id"] = custom.get("flow_id") or start.get("flow_id") or transfer_metadata.get("flow_id")
        transfer_metadata["direction"] = custom.get("Direction") or start.get("direction") or start.get("Direction") or transfer_metadata.get("direction")
        transfer_metadata["target_number"] = normalize_phone(custom.get("DialWhomNumber") or custom.get("To") or custom.get("CallTo") or start.get("to") or start.get("To") or PERSON2_RECEIVER_NUMBER or transfer_metadata.get("target_number"))
        transfer_metadata["from_number"] = normalize_phone(custom.get("From") or custom.get("CallFrom") or start.get("from") or start.get("From") or transfer_metadata.get("from_number"))
        transfer_metadata["to_number"] = normalize_phone(custom.get("To") or custom.get("CallTo") or start.get("to") or start.get("To") or PERSON2_RECEIVER_NUMBER or transfer_metadata.get("to_number"))
        transfer_metadata["call_type"] = custom.get("CallType") or start.get("call_type") or transfer_metadata.get("call_type")
        transfer_metadata["tenant_id"] = custom.get("tenant_id") or start.get("tenant_id") or transfer_metadata.get("tenant_id")
    if session:
        transfer_metadata["target_number"] = normalize_phone(transfer_metadata.get("target_number") or PERSON2_RECEIVER_NUMBER)
        transfer_metadata["from_number"] = normalize_phone(transfer_metadata.get("from_number") or session.get("caller_number"))
        transfer_metadata["to_number"] = normalize_phone(transfer_metadata.get("to_number") or PERSON2_RECEIVER_NUMBER)
    return transfer_metadata


def ensure_session(stream_sid, call_id=None, caller_number=None):
    if not stream_sid:
        return None
    session = sessions.get(stream_sid)
    if not session:
        session = {
            "call_id": call_id,
            "stream_sid": stream_sid,
            "caller_number": caller_number,
            "call_state": "started",
            "routing_status": "routing_in_progress",
            "started_at": iso_now(),
            "last_timestamp_ms": None,
            "last_sequence_number": None,
            "last_chunk_index": None,
            "audio_format": AUDIO_FORMAT,
            "stop_reason": None,
            "events_seen": deque(maxlen=50),
            "chunk_count": 0,
            "continuity_ok": True,
            "missing_sequence_numbers": [],
            "missing_chunk_indices": [],
            "has_seen_first_media": False,
            "last_handoff": None,
            "last_voice_analysis": None,
            "transfer_metadata": {
                "provider": "exotel",
                "flow_id": None,
                "direction": None,
                "target_number": PERSON2_RECEIVER_NUMBER,
                "from_number": None,
                "to_number": PERSON2_RECEIVER_NUMBER,
                "call_type": None,
                "tenant_id": None,
                "stream_sid": stream_sid,
            },
        }
        sessions[stream_sid] = session
    if call_id:
        session["call_id"] = call_id
    if caller_number and not session.get("caller_number"):
        session["caller_number"] = caller_number
    if stream_sid not in debug_buffers:
        debug_buffers[stream_sid] = bytearray()
    if stream_sid not in analysis_buffers:
        analysis_buffers[stream_sid] = bytearray()
    if stream_sid not in segment_buffers:
        segment_buffers[stream_sid] = bytearray()
    if stream_sid not in segment_states:
        segment_states[stream_sid] = {"speech_ms": 0, "silence_ms": 0}
    return session


def update_continuity(session, sequence_number, chunk_index):
    last_seq = session.get("last_sequence_number")
    last_chunk = session.get("last_chunk_index")
    if last_seq is not None and sequence_number is not None and sequence_number != last_seq + 1:
        session["continuity_ok"] = False
        session["missing_sequence_numbers"].append({"expected": last_seq + 1, "received": sequence_number})
    if last_chunk is not None and chunk_index is not None and chunk_index != last_chunk + 1:
        session["continuity_ok"] = False
        session["missing_chunk_indices"].append({"expected": last_chunk + 1, "received": chunk_index})
    if sequence_number is not None:
        session["last_sequence_number"] = sequence_number
    if chunk_index is not None:
        session["last_chunk_index"] = chunk_index


def save_debug_audio(stream_sid):
    raw_audio = debug_buffers.get(stream_sid)
    session = sessions.get(stream_sid)
    if not raw_audio:
        return None
    call_id = (session or {}).get("call_id") or "unknown_call"
    filename = f"{call_id}_{stream_sid}.wav"
    filepath = os.path.join(DEBUG_AUDIO_DIR, filename)
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(bytes(raw_audio))
    return filepath


def build_handoff(session, event_type, call_state, timestamp_ms=None, sequence_number=None, chunk_index=None, audio_chunk_base64=None):
    routing_status = map_routing_status(call_state, session.get("stop_reason"))
    return {
        "schema_version": SCHEMA_VERSION,
        "call_id": session.get("call_id"),
        "stream_sid": session.get("stream_sid"),
        "timestamp_ms": timestamp_ms,
        "caller_number": session.get("caller_number"),
        "event_type": event_type,
        "call_state": call_state,
        "routing_status": routing_status,
        "sequence_number": sequence_number,
        "chunk_index": chunk_index,
        "audio_format": session.get("audio_format", AUDIO_FORMAT),
        "transfer_metadata": dict(session.get("transfer_metadata") or {}),
        "received_at": iso_now(),
        "audio_chunk_base64": audio_chunk_base64,
    }


def save_session_file(payload):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def save_latest_chunk_file(payload):
    with open(LATEST_CHUNK_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def save_queue_file():
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(handoff_queue), f, indent=2, ensure_ascii=False)


def publish_handoff(handoff):
    global latest_chunk
    latest_chunk = handoff
    handoff_queue.append(handoff)
    save_latest_chunk_file(handoff)
    save_queue_file()


def save_latest_analysis_file(payload):
    with open(LATEST_ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def save_analysis_queue_file():
    with open(ANALYSIS_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(voice_analysis_queue), f, indent=2, ensure_ascii=False)


def publish_voice_analysis(payload):
    global latest_voice_analysis
    latest_voice_analysis = payload
    voice_analysis_queue.append(payload)
    save_latest_analysis_file(payload)
    save_analysis_queue_file()


def post_json_async(url, payload, event_name):
    if not url:
        return
    def _post():
        try:
            requests.post(url, json=payload, timeout=FORWARD_TIMEOUT)
        except Exception as e:
            short_log({"event": event_name, "target": url, "call_id": payload.get("call_id"), "stream_sid": payload.get("stream_sid") or payload.get("stream_id"), "error": str(e)})
    threading.Thread(target=_post, daemon=True).start()


def forward_audio_chunk(session, audio_chunk, timestamp_ms=None, sequence_number=None, chunk_index=None):
    if not audio_chunk:
        return
    transfer_metadata = dict(session.get("transfer_metadata") or {})
    receiver_number = normalize_phone(transfer_metadata.get("target_number") or transfer_metadata.get("to_number") or PERSON2_RECEIVER_NUMBER)
    iso_timestamp = iso_now()
    payload_person2 = {
        "call_id": session.get("call_id"),
        "chunk_id": chunk_index if chunk_index is not None else session.get("chunk_count"),
        "timestamp": iso_timestamp,
        "is_final": False,
        "audio_format": "pcm",
        "sample_rate": 8000,
        "channels": 1,
        "bits_per_sample": 16,
        "audio_base64": base64.b64encode(audio_chunk).decode("utf-8"),
        "metadata": {
            "caller_number": session.get("caller_number"),
            "receiver_number": receiver_number,
            "stream_sid": session.get("stream_sid")
        }
    }
    payload_person3 = {
        "schema_version": SCHEMA_VERSION,
        "call_id": session.get("call_id"),
        "stream_id": session.get("stream_sid"),
        "caller_number": session.get("caller_number"),
        "receiver_number": receiver_number,
        "sample_rate": 8000,
        "audio_format": AUDIO_FORMAT,
        "timestamp_ms": timestamp_ms,
        "sequence_number": sequence_number,
        "chunk_index": chunk_index,
        "audio_blob": base64.b64encode(audio_chunk).decode("utf-8"),
        "received_at": iso_timestamp
    }
    post_json_async(PERSON2_URL, payload_person2, "forward_audio_error")
    post_json_async(PERSON3_URL, payload_person3, "forward_audio_error")


def is_speech_chunk(audio_chunk):
    signal = pcm16le_bytes_to_float32(audio_chunk)
    if signal.size == 0:
        return False
    return rms_energy(signal) >= 0.01


def maybe_analyze_segment(session, stream_sid, force=False):
    segment = bytes(segment_buffers.get(stream_sid, b""))
    state = segment_states.get(stream_sid, {"speech_ms": 0, "silence_ms": 0})
    if not segment:
        return
    enough_audio = len(segment) >= MIN_AUDIO_BYTES_FOR_ANALYSIS
    due_to_timeout = state.get("speech_ms", 0) >= MAX_SEGMENT_MS
    due_to_pause = enough_audio and state.get("silence_ms", 0) >= VAD_SILENCE_MS and state.get("speech_ms", 0) >= MIN_SEGMENT_MS
    if not force and not due_to_timeout and not due_to_pause:
        return
    voice_result = analyze_voice(segment, stream_sid=stream_sid, call_id=session.get("call_id"), caller_number=session.get("caller_number"), sample_rate=8000)
    agent_payload = map_voice_analysis_to_agent_schema(voice_result, session, stream_sid, session.get("call_id"))
    full_audio_path, segment_audio_path = save_voice_segment_artifacts(stream_sid, session.get("call_id"), segment)
    voice_result["full_audio_path"] = full_audio_path
    voice_result["segment_audio_path"] = segment_audio_path
    voice_result["agent_payload"] = agent_payload
    session["last_voice_analysis"] = voice_result
    publish_voice_analysis(voice_result)
    post_json_async(PERSON4_URL, agent_payload, "forward_voice_analysis_error")
    segment_buffers[stream_sid] = bytearray()
    segment_states[stream_sid] = {"speech_ms": 0, "silence_ms": 0}


@app.route("/", methods=["GET"])
def root():
    return jsonify({"ok": True, "service": "exotel-stream-handoff", "time": iso_now()})


@app.route("/health", methods=["GET"])
def health():
    active_sessions = sum(1 for s in sessions.values() if s.get("call_state") not in {"stopped", "transfer_failed", "no_answer", "call_ended_early", "stream_dropped"})
    return jsonify({
        "ok": True,
        "time": iso_now(),
        "active_sessions": active_sessions,
        "total_sessions": len(sessions),
        "latest_chunk_available": latest_chunk is not None,
        "queue_size": len(handoff_queue),
        "latest_voice_analysis_available": latest_voice_analysis is not None,
        "voice_analysis_queue_size": len(voice_analysis_queue),
        "reference_voice_exists": os.path.exists(REFERENCE_VOICE_FILE),
        "receiver_number": PERSON2_RECEIVER_NUMBER
    })


@app.route("/exotel/webhook", methods=["GET", "POST"])
def exotel_webhook():
    payload = request.values.to_dict(flat=True)
    save_session_file(payload)
    short_log({
        "event": "exotel_passthru_webhook",
        "call_id": payload.get("CallSid"),
        "caller_number": normalize_phone(payload.get("CallFrom") or payload.get("From")),
        "to_number": normalize_phone(payload.get("CallTo") or payload.get("To") or PERSON2_RECEIVER_NUMBER),
        "direction": payload.get("Direction"),
        "call_type": payload.get("CallType"),
        "flow_id": payload.get("flow_id"),
        "tenant_id": payload.get("tenant_id"),
        "current_time": payload.get("CurrentTime")
    })
    passthru_stream_sid = payload.get("Stream[StreamSID]")
    if passthru_stream_sid:
        session = ensure_session(passthru_stream_sid, call_id=payload.get("CallSid"), caller_number=normalize_phone(payload.get("CallFrom") or payload.get("From")))
        session["transfer_metadata"] = build_transfer_metadata(existing=session.get("transfer_metadata"), payload=payload, session=session)
    return jsonify({"ok": True}), 200


@app.route("/latest-chunk", methods=["GET"])
def get_latest_chunk():
    if latest_chunk is None:
        return jsonify({"ok": False, "message": "no chunk available yet"}), 404
    return jsonify(latest_chunk)


@app.route("/queue", methods=["GET"])
def get_queue():
    limit = safe_int(request.args.get("limit"), 20)
    limit = max(1, min(limit, 200))
    items = list(handoff_queue)[-limit:]
    return jsonify({"ok": True, "count": len(items), "items": items})


@app.route("/call/<stream_sid>", methods=["GET"])
def get_call(stream_sid):
    session = sessions.get(stream_sid)
    if not session:
        return jsonify({"ok": False, "message": "stream_sid not found"}), 404
    response = dict(session)
    response["events_seen"] = list(response.get("events_seen", []))
    response["debug_audio_saved"] = bool(debug_buffers.get(stream_sid))
    response["segment_buffer_bytes"] = len(segment_buffers.get(stream_sid, b""))
    return jsonify(response)


@app.route("/latest-voice-analysis", methods=["GET"])
def get_latest_voice_analysis():
    if latest_voice_analysis is None:
        return jsonify({"ok": False, "message": "no voice analysis available yet"}), 404
    return jsonify(latest_voice_analysis)


@app.route("/voice-analysis-queue", methods=["GET"])
def get_voice_analysis_queue():
    limit = safe_int(request.args.get("limit"), 20)
    limit = max(1, min(limit, 200))
    items = list(voice_analysis_queue)[-limit:]
    return jsonify({"ok": True, "count": len(items), "items": items})


@sock.route("/ws")
def ws(ws):
    while True:
        raw_message = ws.receive()
        if raw_message is None:
            break
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            short_log({"event": "invalid_json", "call_state": "stream_dropped", "message_preview": str(raw_message)[:200]})
            continue
        event_type = str(data.get("event", "")).lower().strip()
        stream_sid = get_stream_sid(data)
        call_id = get_call_id(data)
        caller_number = get_caller_number(data)
        session = ensure_session(stream_sid, call_id=call_id, caller_number=caller_number)
        if session is None:
            short_log({"event": "missing_stream_sid", "call_id": call_id, "caller_number": caller_number, "call_state": "stream_dropped"})
            continue
        session["transfer_metadata"] = build_transfer_metadata(existing=session.get("transfer_metadata"), data=data, session=session)
        session["events_seen"].append(event_type)

        if event_type == "connected":
            session["call_state"] = "started"
            session["routing_status"] = map_routing_status(session["call_state"])
            short_log({"event": "connected", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "call_state": session["call_state"], "routing_status": session["routing_status"]})
            continue

        if event_type == "start":
            start = data.get("start") or {}
            custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}
            incoming_call_id = start.get("callSid") or start.get("CallSid") or start.get("call_id") or start.get("callId") or custom.get("CallSid") or custom.get("callSid") or custom.get("call_id") or custom.get("callId")
            if incoming_call_id:
                session["call_id"] = incoming_call_id
            if not session.get("caller_number"):
                session["caller_number"] = normalize_phone(start.get("from") or custom.get("From") or custom.get("CallFrom"))
            session["transfer_metadata"] = build_transfer_metadata(existing=session.get("transfer_metadata"), data=data, session=session)
            session["call_state"] = "started"
            session["routing_status"] = map_routing_status(session["call_state"])
            short_log({"event": "start", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "call_state": session["call_state"], "routing_status": session["routing_status"], "audio_format": session["audio_format"]})
            continue

        if event_type == "dtmf":
            dtmf = data.get("dtmf") or {}
            short_log({"event": "dtmf", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "call_state": session["call_state"], "routing_status": session.get("routing_status"), "digit": dtmf.get("digits") or dtmf.get("digit")})
            continue

        if event_type == "media":
            media = data.get("media") or {}
            timestamp_ms = safe_int(media.get("timestamp") or data.get("timestamp"), None)
            sequence_number = safe_int(data.get("sequenceNumber") or data.get("sequence_number"), None)
            chunk_index = safe_int(media.get("chunk") or media.get("chunk_index") or data.get("chunk_index"), None)
            audio_chunk_base64 = media.get("payload")
            if not audio_chunk_base64:
                short_log({"event": "media_missing_payload", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "timestamp_ms": timestamp_ms, "sequence_number": sequence_number, "chunk_index": chunk_index, "call_state": "stream_dropped"})
                continue
            try:
                audio_chunk = base64.b64decode(audio_chunk_base64)
            except Exception:
                short_log({"event": "media_decode_error", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "timestamp_ms": timestamp_ms, "sequence_number": sequence_number, "chunk_index": chunk_index, "call_state": "stream_dropped"})
                continue
            if not session["has_seen_first_media"]:
                session["call_state"] = "connected"
                session["has_seen_first_media"] = True
            else:
                session["call_state"] = "speaking"
            session["routing_status"] = map_routing_status(session["call_state"])
            session["last_timestamp_ms"] = timestamp_ms
            session["chunk_count"] += 1
            update_continuity(session, sequence_number, chunk_index)
            if len(debug_buffers[stream_sid]) < DEBUG_BUFFER_LIMIT_BYTES:
                remaining = DEBUG_BUFFER_LIMIT_BYTES - len(debug_buffers[stream_sid])
                debug_buffers[stream_sid].extend(audio_chunk[:remaining])
            analysis_buffers[stream_sid].extend(audio_chunk)
            forward_audio_chunk(session, audio_chunk, timestamp_ms, sequence_number, chunk_index)
            segment_buffers[stream_sid].extend(audio_chunk)
            frame_ms = 20
            if is_speech_chunk(audio_chunk):
                segment_states[stream_sid]["speech_ms"] += frame_ms
                segment_states[stream_sid]["silence_ms"] = 0
            else:
                segment_states[stream_sid]["silence_ms"] += frame_ms
            maybe_analyze_segment(session, stream_sid, force=False)
            handoff = build_handoff(session=session, event_type="media", call_state=session["call_state"], timestamp_ms=timestamp_ms, sequence_number=sequence_number, chunk_index=chunk_index, audio_chunk_base64=audio_chunk_base64)
            session["last_handoff"] = handoff
            publish_handoff(handoff)
            short_log({"event": "media", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "timestamp_ms": timestamp_ms, "sequence_number": sequence_number, "chunk_index": chunk_index, "decoded_bytes": len(audio_chunk), "call_state": session["call_state"], "routing_status": session["routing_status"]})
            continue

        if event_type == "stop":
            stop_reason = infer_stop_reason(data)
            final_state = map_fallback_state(stop_reason, session.get("call_state"))
            session["stop_reason"] = stop_reason
            session["call_state"] = final_state
            session["routing_status"] = map_routing_status(session["call_state"], stop_reason)
            saved_file = save_debug_audio(stream_sid)
            maybe_analyze_segment(session, stream_sid, force=True)
            stop_payload = {
                "schema_version": SCHEMA_VERSION,
                "call_id": session["call_id"],
                "stream_sid": session["stream_sid"],
                "timestamp_ms": session.get("last_timestamp_ms"),
                "caller_number": session["caller_number"],
                "event_type": "stop",
                "call_state": final_state if final_state != "stopped" else "stopped",
                "routing_status": session["routing_status"],
                "sequence_number": session.get("last_sequence_number"),
                "chunk_index": session.get("last_chunk_index"),
                "audio_format": session.get("audio_format", AUDIO_FORMAT),
                "transfer_metadata": dict(session.get("transfer_metadata") or {}),
                "received_at": iso_now(),
                "audio_chunk_base64": None,
                "stop_reason": stop_reason
            }
            session["last_handoff"] = stop_payload
            publish_handoff(stop_payload)
            full_audio = bytes(analysis_buffers.get(stream_sid, b""))
            full_audio_path, segment_audio_path = save_voice_segment_artifacts(stream_sid, session.get("call_id"), full_audio)
            short_log({"event": "stop", "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "call_state": session["call_state"], "routing_status": session["routing_status"], "stop_reason": session["stop_reason"], "continuity_ok": session["continuity_ok"], "saved_debug_audio": saved_file, "full_audio_path": full_audio_path, "segment_audio_path": segment_audio_path})
            continue

        short_log({"event": "unhandled_event", "incoming_event_type": event_type, "call_id": session["call_id"], "stream_sid": session["stream_sid"], "caller_number": session["caller_number"], "call_state": session["call_state"], "routing_status": session.get("routing_status")})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.run(host="0.0.0.0", port=port, debug=True)