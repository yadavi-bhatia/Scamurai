from app import on_audio_chunk

def replay_pcm_file(path, call_id="TEST_CALL", stream_sid="TEST_STREAM", caller_number="+910000000000"):
    with open(path, "rb") as f:
        data = f.read()

    chunk_size = 320
    timestamp_ms = 0
    chunk_index = 1

    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]

        meta = {
            "provider": "exotel",
            "call_id": call_id,
            "stream_sid": stream_sid,
            "caller_number": caller_number,
            "timestamp": str(timestamp_ms),
            "event_type": "media",
            "sequence_number": chunk_index,
            "chunk_index": chunk_index
        }

        on_audio_chunk(chunk, meta)

        timestamp_ms += 20
        chunk_index += 1


if __name__ == "__main__":
    replay_pcm_file("debug_audio/TEST_STREAM.pcm")