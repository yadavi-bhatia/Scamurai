import whisper

model = whisper.load_model("base")

def transcribe_audio(audio_bytes):
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        f.write(audio_bytes)
        f.flush()
        result = model.transcribe(f.name)

    return result["text"]