import os
import json
import base64
import wave
from datetime import datetime, timezone
from collections import deque


from flask import Flask, request, jsonify
from flask_sock import Sock
from app.main import run_pipeline


app = Flask(__name__)
sock = Sock(app)


AUDIO_FORMAT = "raw/slin;rate=8000;channels=1;sample_width=16le"
DEBUG_BUFFER_LIMIT_BYTES = 32000
LATEST_QUEUE_MAXLEN = 200
DEBUG_AUDIO_DIR = os.environ.get("DEBUG_AUDIO_DIR", "debug_audio")
SCHEMA_VERSION = "1.0"


os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)


sessions = {}
latest_chunk = None
handoff_queue = deque(maxlen=LATEST_QUEUE_MAXLEN)
debug_buffers = {}



def iso_now():
    return datetime.now(timezone.utc).isoformat()



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



def infer_stop_reason(payload):
    candidates = [
        payload.get("reason"),
        payload.get("stop_reason"),
        payload.get("message"),
    ]
    stop = payload.get("stop") or {}
    media = payload.get("media") or {}
    start = payload.get("start") or {}


    candidates.extend([
        stop.get("reason"),
        stop.get("stop_reason"),
        media.get("reason"),
        start.get("reason"),
    ])


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
    return (
        data.get("streamSid")
        or data.get("stream_sid")
        or (data.get("start") or {}).get("streamSid")
        or (data.get("start") or {}).get("stream_sid")
        or (data.get("media") or {}).get("streamSid")
        or (data.get("stop") or {}).get("streamSid")
    )



def get_call_id(data):
    start = data.get("start") or {}
    stop = data.get("stop") or {}
    media = data.get("media") or {}


    custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}
    if not isinstance(custom, dict):
        custom = {}


    return (
        data.get("callSid")
        or data.get("CallSid")
        or data.get("call_id")
        or data.get("callId")
        or start.get("callSid")
        or start.get("CallSid")
        or start.get("call_id")
        or start.get("callId")
        or stop.get("callSid")
        or stop.get("CallSid")
        or stop.get("call_id")
        or stop.get("callId")
        or media.get("callSid")
        or media.get("CallSid")
        or media.get("call_id")
        or media.get("callId")
        or custom.get("CallSid")
        or custom.get("callSid")
        or custom.get("call_id")
        or custom.get("callId")
    )



def get_caller_number(data):
    start = data.get("start") or {}
    custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}
    return normalize_phone(
        data.get("caller_number")
        or data.get("from")
        or data.get("From")
        or start.get("from")
        or start.get("From")
        or custom.get("From")
        or custom.get("CallFrom")
        or custom.get("caller_number")
    )



def build_transfer_metadata(existing=None, payload=None, data=None, session=None):
    transfer_metadata = dict(existing or {})


    if "provider" not in transfer_metadata:
        transfer_metadata["provider"] = "exotel"


    if payload:
        transfer_metadata["flow_id"] = (
            payload.get("flow_id")
            or transfer_metadata.get("flow_id")
        )
        transfer_metadata["direction"] = (
            payload.get("Direction")
            or transfer_metadata.get("direction")
        )
        transfer_metadata["target_number"] = normalize_phone(
            payload.get("DialWhomNumber")
            or payload.get("CallTo")
            or payload.get("To")
            or transfer_metadata.get("target_number")
        )
        transfer_metadata["from_number"] = normalize_phone(
            payload.get("CallFrom")
            or payload.get("From")
            or transfer_metadata.get("from_number")
        )
        transfer_metadata["to_number"] = normalize_phone(
            payload.get("CallTo")
            or payload.get("To")
            or transfer_metadata.get("to_number")
        )
        transfer_metadata["call_type"] = (
            payload.get("CallType")
            or transfer_metadata.get("call_type")
        )
        transfer_metadata["tenant_id"] = (
            payload.get("tenant_id")
            or transfer_metadata.get("tenant_id")
        )
        transfer_metadata["stream_sid"] = (
            payload.get("Stream[StreamSID]")
            or transfer_metadata.get("stream_sid")
        )


    if data:
        start = data.get("start") or {}
        custom = start.get("customParameters", {}) if isinstance(start.get("customParameters"), dict) else {}


        transfer_metadata["flow_id"] = (
            custom.get("flow_id")
            or start.get("flow_id")
            or transfer_metadata.get("flow_id")
        )
        transfer_metadata["direction"] = (
            custom.get("Direction")
            or start.get("direction")
            or start.get("Direction")
            or transfer_metadata.get("direction")
        )
        transfer_metadata["target_number"] = normalize_phone(
            custom.get("DialWhomNumber")
            or custom.get("To")
            or custom.get("CallTo")
            or start.get("to")
            or start.get("To")
            or transfer_metadata.get("target_number")
        )
        transfer_metadata["from_number"] = normalize_phone(
            custom.get("From")
            or custom.get("CallFrom")
            or start.get("from")
            or start.get("From")
            or transfer_metadata.get("from_number")
        )
        transfer_metadata["to_number"] = normalize_phone(
            custom.get("To")
            or custom.get("CallTo")
            or start.get("to")
            or start.get("To")
            or transfer_metadata.get("to_number")
        )
        transfer_metadata["call_type"] = (
            custom.get("CallType")
            or start.get("call_type")
            or transfer_metadata.get("call_type")
        )
        transfer_metadata["tenant_id"] = (
            custom.get("tenant_id")
            or start.get("tenant_id")
            or transfer_metadata.get("tenant_id")
        )


    if session:
        transfer_metadata["target_number"] = normalize_phone(
            transfer_metadata.get("target_number")
            or session.get("target_number")
        )
        transfer_metadata["from_number"] = normalize_phone(
            transfer_metadata.get("from_number")
            or session.get("caller_number")
        )


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
            "transfer_metadata": {
                "provider": "exotel",
                "flow_id": None,
                "direction": None,
                "target_number": None,
                "from_number": None,
                "to_number": None,
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


    return session



def update_continuity(session, sequence_number, chunk_index):
    last_seq = session.get("last_sequence_number")
    last_chunk = session.get("last_chunk_index")


    if last_seq is not None and sequence_number is not None and sequence_number != last_seq + 1:
        session["continuity_ok"] = False
        session["missing_sequence_numbers"].append({
            "expected": last_seq + 1,
            "received": sequence_number
        })


    if last_chunk is not None and chunk_index is not None and chunk_index != last_chunk + 1:
        session["continuity_ok"] = False
        session["missing_chunk_indices"].append({
            "expected": last_chunk + 1,
            "received": chunk_index
        })


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



def publish_handoff(handoff):
    global latest_chunk
    latest_chunk = handoff
    handoff_queue.append(handoff)



@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "ok": True,
        "service": "exotel-stream-handoff",
        "time": iso_now()
    })



@app.route("/health", methods=["GET"])
def health():
    active_sessions = sum(1 for s in sessions.values() if s.get("call_state") not in {"stopped", "transfer_failed", "no_answer", "call_ended_early", "stream_dropped"})
    return jsonify({
        "ok": True,
        "time": iso_now(),
        "active_sessions": active_sessions,
        "total_sessions": len(sessions),
        "latest_chunk_available": latest_chunk is not None,
        "queue_size": len(handoff_queue)
    })



@app.route("/exotel/webhook", methods=["GET", "POST"])
def exotel_webhook():
    payload = request.values.to_dict(flat=True)


    short_log({
        "event": "exotel_passthru_webhook",
        "call_id": payload.get("CallSid"),
        "caller_number": normalize_phone(payload.get("CallFrom") or payload.get("From")),
        "to_number": normalize_phone(payload.get("CallTo") or payload.get("To")),
        "direction": payload.get("Direction"),
        "call_type": payload.get("CallType"),
        "flow_id": payload.get("flow_id"),
        "tenant_id": payload.get("tenant_id"),
        "current_time": payload.get("CurrentTime")
    })


    passthru_stream_sid = payload.get("Stream[StreamSID]")
    if passthru_stream_sid:
        session = ensure_session(
            passthru_stream_sid,
            call_id=payload.get("CallSid"),
            caller_number=normalize_phone(payload.get("CallFrom") or payload.get("From"))
        )
        session["transfer_metadata"] = build_transfer_metadata(
            existing=session.get("transfer_metadata"),
            payload=payload,
            session=session
        )


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
    return jsonify({
        "ok": True,
        "count": len(items),
        "items": items
    })



@app.route("/call/<stream_sid>", methods=["GET"])
def get_call(stream_sid):
    session = sessions.get(stream_sid)
    if not session:
        return jsonify({"ok": False, "message": "stream_sid not found"}), 404


    response = dict(session)
    response["events_seen"] = list(response.get("events_seen", []))
    response["debug_audio_saved"] = bool(debug_buffers.get(stream_sid))
    return jsonify(response)



@sock.route("/ws")
def ws(ws):
    print("🔥 WS CONNECTED")
    while True:
        raw_message = ws.receive()
        if raw_message is None:
            break

        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            short_log({
                "event": "invalid_json",
                "call_state": "stream_dropped",
                "message_preview": str(raw_message)[:200]
            })
            continue

        event_type = str(data.get("event", "")).lower().strip()
        stream_sid = get_stream_sid(data)
        call_id = get_call_id(data)
        caller_number = get_caller_number(data)

        session = ensure_session(stream_sid, call_id=call_id, caller_number=caller_number)

        if session is None:
            short_log({
                "event": "missing_stream_sid",
                "call_id": call_id,
                "caller_number": caller_number,
                "call_state": "stream_dropped"
            })
            continue

        session["transfer_metadata"] = build_transfer_metadata(
            existing=session.get("transfer_metadata"),
            data=data,
            session=session
        )

        session["events_seen"].append(event_type)

        if event_type == "connected":
            session["call_state"] = "started"
            session["routing_status"] = map_routing_status(session["call_state"])
            short_log({
                "event": "connected",
                "call_id": session["call_id"],
                "stream_sid": session["stream_sid"]
            })
            continue

        if event_type == "start":
            session["call_state"] = "started"
            session["routing_status"] = map_routing_status(session["call_state"])
            short_log({
                "event": "start",
                "call_id": session["call_id"],
                "stream_sid": session["stream_sid"]
            })
            continue

        if event_type == "dtmf":
            dtmf = data.get("dtmf") or {}
            short_log({
                "event": "dtmf",
                "digit": dtmf.get("digits") or dtmf.get("digit")
            })
            continue

        # ✅ FIXED MEDIA BLOCK (NOW CORRECTLY PLACED)
        if event_type == "media":
            media = data.get("media") or {}

            print("EVENT: media received")

            timestamp_ms = safe_int(
                media.get("timestamp") or data.get("timestamp"),
                None
            )

            sequence_number = safe_int(
                data.get("sequenceNumber") or data.get("sequence_number"),
                None
            )

            chunk_index = safe_int(
                media.get("chunk") or media.get("chunk_index") or data.get("chunk_index"),
                None
            )

            audio_chunk_base64 = media.get("payload")
            if not audio_chunk_base64:
                print("no payload in media")
                continue

            try:
                audio_chunk = base64.b64decode(audio_chunk_base64)

                decision = run_pipeline(audio_chunk)
                session["last_decision"] = decision

                print("🧠 decision:", decision)

            except Exception as e:
                print("pipeline error:", e)
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

            handoff = build_handoff(
                session=session,
                event_type="media",
                call_state=session["call_state"],
                timestamp_ms=timestamp_ms,
                sequence_number=sequence_number,
                chunk_index=chunk_index,
                audio_chunk_base64=audio_chunk_base64
            )

            handoff["decision"] = session.get("last_decision")

            session["last_handoff"] = handoff
            publish_handoff(handoff)

            print("✅ handoff published")

            continue

        if event_type == "stop":
            stop_reason = infer_stop_reason(data)
            session["stop_reason"] = stop_reason
            session["call_state"] = "stopped"

            publish_handoff({
                "event_type": "stop",
                "call_id": session["call_id"],
                "stream_sid": session["stream_sid"],
                "stop_reason": stop_reason
            })

            short_log({
                "event": "stop",
                "call_id": session["call_id"],
                "stream_sid": session["stream_sid"]
            })
            continue

        short_log({
            "event": "unhandled_event",
            "incoming_event_type": event_type
        })



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)