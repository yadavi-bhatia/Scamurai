"""
Person 2 - Stream Processor
Handles real-time audio/video stream processing for live call analysis
Supports WebSocket, HTTP streaming, and file-based streaming
"""

import json
import asyncio
import threading
import queue
import time
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import config


class StreamState(Enum):
    """Stream states"""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PROCESSING = "processing"
    PAUSED = "paused"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class StreamType(Enum):
    """Types of streams supported"""
    WEBSOCKET = "websocket"
    HTTP = "http"
    FILE = "file"
    MICROPHONE = "microphone"
    EXOTEL = "exotel"


@dataclass
class StreamChunk:
    """Represents a single chunk of stream data"""
    chunk_id: str
    session_id: str
    timestamp: str
    data: bytes
    sample_rate: int
    is_final: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TranscriptChunk:
    """Represents a transcribed chunk"""
    chunk_id: str
    session_id: str
    timestamp: str
    text: str
    speaker: str
    is_final: bool
    confidence: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class StreamProcessor:
    """
    Real-time stream processor for live call analysis
    Handles WebSocket, HTTP, and file-based streaming
    """
    
    def __init__(self, 
                 session_id: str,
                 stream_type: StreamType = StreamType.WEBSOCKET,
                 on_transcript: Optional[Callable] = None,
                 on_alert: Optional[Callable] = None):
        
        self.session_id = session_id
        self.stream_type = stream_type
        self.on_transcript = on_transcript
        self.on_alert = on_alert
        
        # State management
        self.state = StreamState.IDLE
        self.chunk_queue = queue.Queue()
        self.transcript_queue = queue.Queue()
        self.processing_thread = None
        self.is_running = False
        
        # Statistics
        self.chunks_processed = 0
        self.transcripts_generated = 0
        self.start_time = None
        self.end_time = None
        
        # Buffer for audio
        self.audio_buffer = b''
        self.buffer_duration = 0.0
        self.chunk_duration = config.ASR_CONFIG.get("chunk_duration", 3)
        self.sample_rate = config.ASR_CONFIG.get("sample_rate", 16000)
        
        # Import ASR engine lazily
        self.asr_engine = None
        
        print(f"🌊 Stream Processor initialized")
        print(f"   Session: {session_id}")
        print(f"   Type: {stream_type.value}")
        print(f"   Chunk duration: {self.chunk_duration}s")
    
    def _init_asr(self):
        """Initialize ASR engine"""
        if self.asr_engine is None:
            from asr_engine import get_asr_engine
            self.asr_engine = get_asr_engine()
    
    def start(self):
        """Start the stream processor"""
        if self.is_running:
            print("⚠️ Stream processor already running")
            return
        
        self.is_running = True
        self.state = StreamState.CONNECTING
        self.start_time = datetime.now()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
        
        print(f"✅ Stream processor started for session {self.session_id}")
    
    def stop(self):
        """Stop the stream processor"""
        self.is_running = False
        self.state = StreamState.DISCONNECTED
        self.end_time = datetime.now()
        
        # Process any remaining audio
        if len(self.audio_buffer) > 0:
            self._transcribe_buffer()
        
        print(f"🛑 Stream processor stopped for session {self.session_id}")
        print(f"   Total chunks: {self.chunks_processed}")
        print(f"   Transcripts: {self.transcripts_generated}")
        print(f"   Duration: {(self.end_time - self.start_time).total_seconds():.1f}s")
    
    def _resample_audio(self, audio_data: bytes, from_rate: int, to_rate: int) -> bytes:
        """
        Resample audio data safely
        Handles odd frame counts by padding or truncating
        """
        import audioop
        
        # Calculate expected frame size
        bytes_per_sample = 2  # 16-bit audio
        expected_bytes = (len(audio_data) // bytes_per_sample) * bytes_per_sample
        
        # Trim to even number of samples if needed
        if len(audio_data) != expected_bytes:
            audio_data = audio_data[:expected_bytes]
        
        if len(audio_data) == 0:
            return b''
        
        try:
            # Resample
            converted, _ = audioop.ratecv(audio_data, bytes_per_sample, 1, from_rate, to_rate, None)
            return converted
        except Exception as e:
            print(f"⚠️ Resample error: {e}")
            return audio_data
    
    def process_chunk(self, 
                      audio_data: bytes, 
                      sample_rate: int = 8000,
                      metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Process an incoming audio chunk (for HTTP/file streaming)
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Sample rate of the audio (default 8kHz for telephony)
            metadata: Additional metadata (call_id, etc.)
        
        Returns:
            Transcription result if chunk is complete, None otherwise
        """
        self._init_asr()
        
        # Ensure audio data is not empty
        if not audio_data or len(audio_data) < 100:
            return None
        
        # Resample if needed
        if sample_rate != self.sample_rate:
            audio_data = self._resample_audio(audio_data, sample_rate, self.sample_rate)
        
        # Add to buffer
        self.audio_buffer += audio_data
        chunk_duration = len(audio_data) / (self.sample_rate * 2)  # 16-bit = 2 bytes per sample
        self.buffer_duration += chunk_duration
        
        self.chunks_processed += 1
        
        # Check if we have enough audio to transcribe
        if self.buffer_duration >= self.chunk_duration:
            return self._transcribe_buffer()
        
        return None
    
    def process_websocket_chunk(self, message: Dict) -> Optional[Dict]:
        """
        Process a WebSocket message (for Exotel integration)
        
        Expected message format:
        {
            "event": "media",
            "stream_sid": "xxx",
            "media": {
                "payload": "base64_audio_data"
            }
        }
        """
        event = message.get("event")
        
        if event == "media":
            import base64
            payload = message.get("media", {}).get("payload", "")
            if payload:
                try:
                    audio_bytes = base64.b64decode(payload)
                    return self.process_chunk(audio_bytes, sample_rate=8000, metadata=message)
                except Exception as e:
                    print(f"⚠️ Failed to decode audio: {e}")
                    return None
            return None
        
        elif event == "start":
            self.state = StreamState.CONNECTED
            print(f"📞 Stream started: {message.get('stream_sid')}")
            return {"event": "start_ack", "status": "ok"}
        
        elif event == "stop":
            self.stop()
            return {"event": "stop_ack", "status": "ok"}
        
        return None
    
    def _transcribe_buffer(self) -> Optional[Dict]:
        """Transcribe the current audio buffer"""
        if len(self.audio_buffer) < 1000:  # Minimum audio length (about 0.1 seconds)
            return None
        
        # Save buffer to temp file for transcription
        temp_path = None
        try:
            import wave
            import tempfile
            
            # Create temp WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name
            
            # Write WAV file
            with wave.open(temp_path, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(self.sample_rate)
                wav.writeframes(self.audio_buffer)
            
            # Transcribe
            text = self.asr_engine.transcribe_file(temp_path)
            
            # Clean up
            os.unlink(temp_path)
            
            # Clear buffer
            self.audio_buffer = b''
            self.buffer_duration = 0.0
            
            if text and not text.startswith("[ASR"):
                self.transcripts_generated += 1
                
                result = {
                    "session_id": self.session_id,
                    "chunk_id": f"{self.session_id}_{self.transcripts_generated:04d}",
                    "timestamp": datetime.now().isoformat(),
                    "transcript": text,
                    "speaker": "caller",
                    "is_final": True,
                    "confidence": 0.85,
                    "chunks_processed": self.chunks_processed
                }
                
                # Call callback
                if self.on_transcript:
                    self.on_transcript(result)
                
                return result
            
        except Exception as e:
            print(f"⚠️ Transcription error: {e}")
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        # Clear buffer even on error to avoid stuck state
        self.audio_buffer = b''
        self.buffer_duration = 0.0
        return None
    
    def _process_loop(self):
        """Background processing loop"""
        self.state = StreamState.PROCESSING
        
        while self.is_running:
            try:
                # Process any pending chunks
                try:
                    chunk = self.chunk_queue.get(timeout=0.1)
                    result = self.process_chunk(chunk["data"], chunk.get("sample_rate", 8000))
                    if result and self.on_transcript:
                        self.on_transcript(result)
                except queue.Empty:
                    pass
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.01)
                
            except Exception as e:
                print(f"⚠️ Processing error: {e}")
        
        self.state = StreamState.DISCONNECTED
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        duration = 0
        if self.start_time:
            end = self.end_time or datetime.now()
            duration = (end - self.start_time).total_seconds()
        
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "stream_type": self.stream_type.value,
            "chunks_processed": self.chunks_processed,
            "transcripts_generated": self.transcripts_generated,
            "duration_seconds": round(duration, 1),
            "is_running": self.is_running
        }


class ExotelStreamHandler:
    """
    Specialized handler for Exotel call streams
    Handles the specific format Exotel uses for real-time audio
    """
    
    def __init__(self, 
                 call_sid: str,
                 on_transcript: Optional[Callable] = None,
                 on_alert: Optional[Callable] = None):
        
        self.call_sid = call_sid
        self.on_transcript = on_transcript
        self.on_alert = on_alert
        
        # Create stream processor
        self.processor = StreamProcessor(
            session_id=call_sid,
            stream_type=StreamType.EXOTEL,
            on_transcript=self._handle_transcript,
            on_alert=on_alert
        )
        
        self.is_active = False
        self.alert_triggered = False
        
        print(f"📞 Exotel Stream Handler initialized for call: {call_sid}")
    
    def start(self):
        """Start handling the call stream"""
        self.is_active = True
        self.processor.start()
        print(f"✅ Started monitoring call: {self.call_sid}")
    
    def stop(self):
        """Stop handling the call stream"""
        self.is_active = False
        self.processor.stop()
        print(f"🛑 Stopped monitoring call: {self.call_sid}")
    
    def process_message(self, message: Dict) -> Optional[Dict]:
        """
        Process an Exotel WebSocket message
        
        Exotel format example:
        {
            "event": "media",
            "call_sid": "xxx",
            "stream_sid": "xxx",
            "media": {
                "payload": "base64_audio"
            }
        }
        """
        if not self.is_active:
            return None
        
        return self.processor.process_websocket_chunk(message)
    
    def _handle_transcript(self, transcript: Dict):
        """Handle transcript from stream processor"""
        print(f"\n📝 [{self.call_sid}] Caller: {transcript['transcript'][:80]}...")
        
        if self.on_transcript:
            self.on_transcript(transcript)
        
        # Check for high-risk keywords (Hindi + English)
        risk_keywords = [
            "bitcoin", "gift card", "arrest", "social security", 
            "otp", "aadhaar", "pan", "rupees", "jail", "police",
            "send money", "transfer", "verify", "कृपया", "जल्दी"
        ]
        text_lower = transcript['transcript'].lower()
        
        detected = [kw for kw in risk_keywords if kw in text_lower]
        if detected and not self.alert_triggered:
            self.alert_triggered = True
            alert = {
                "type": "HIGH_RISK_DETECTED",
                "call_sid": self.call_sid,
                "keywords": detected,
                "transcript": transcript['transcript'],
                "timestamp": datetime.now().isoformat()
            }
            
            if self.on_alert:
                self.on_alert(alert)
            else:
                self._print_alert(alert)
    
    def _print_alert(self, alert: Dict):
        """Print alert to console"""
        print("\n" + "="*60)
        print("🚨 ALERT: HIGH RISK SCAM DETECTED")
        print("="*60)
        print(f"Call SID: {alert['call_sid']}")
        print(f"Keywords detected: {', '.join(alert['keywords'])}")
        print(f"Transcript: {alert['transcript'][:100]}...")
        print("="*60 + "\n")
    
    def get_summary(self) -> Dict:
        """Get call summary"""
        stats = self.processor.get_stats()
        return {
            "call_sid": self.call_sid,
            "is_active": self.is_active,
            "alert_triggered": self.alert_triggered,
            "stats": stats
        }


class FileStreamProcessor:
    """
    Process audio files as if they were live streams
    Useful for testing and demo
    """
    
    def __init__(self, 
                 audio_file_path: str,
                 on_transcript: Optional[Callable] = None,
                 on_alert: Optional[Callable] = None):
        
        self.audio_file_path = audio_file_path
        self.on_transcript = on_transcript
        self.on_alert = on_alert
        
        self.processor = StreamProcessor(
            session_id=os.path.basename(audio_file_path).replace('.', '_'),
            stream_type=StreamType.FILE,
            on_transcript=on_transcript,
            on_alert=on_alert
        )
    
    def process(self, chunk_duration: float = 3.0) -> List[Dict]:
        """
        Process the audio file in chunks (simulate live stream)
        
        Returns:
            List of transcription results
        """
        import wave
        
        results = []
        
        try:
            # Open audio file
            with wave.open(self.audio_file_path, 'rb') as wav:
                sample_rate = wav.getframerate()
                n_channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                
                print(f"📁 Processing file: {self.audio_file_path}")
                print(f"   Sample rate: {sample_rate}Hz, Channels: {n_channels}")
                
                # Calculate chunk size
                chunk_size = int(sample_rate * chunk_duration)
                
                # Process in chunks
                chunk_num = 0
                while True:
                    frames = wav.readframes(chunk_size)
                    if not frames:
                        break
                    
                    # Convert to mono if needed
                    if n_channels > 1:
                        import audioop
                        frames = audioop.tomono(frames, sample_width, 1, 1)
                    
                    chunk_num += 1
                    print(f"   Processing chunk {chunk_num}...")
                    
                    # Process chunk
                    result = self.processor.process_chunk(frames, sample_rate)
                    if result:
                        results.append(result)
                        if self.on_transcript:
                            self.on_transcript(result)
                    
                    # Simulate real-time delay
                    time.sleep(0.1)
                
                # Finalize any remaining audio
                final_result = self.processor._transcribe_buffer()
                if final_result:
                    results.append(final_result)
                
                self.processor.stop()
                
        except Exception as e:
            print(f"❌ Error processing file: {e}")
        
        print(f"✅ File processed: {len(results)} transcripts generated")
        return results


# Quick test
if __name__ == "__main__":
    print("=" * 60)
    print("🌊 STREAM PROCESSOR TEST")
    print("=" * 60)
    
    # Test with mock data
    def on_transcript(transcript):
        print(f"📝 Transcript: {transcript['transcript'][:50]}...")
    
    def on_alert(alert):
        print(f"🚨 ALERT: {alert['type']} - {', '.join(alert['keywords'])}")
    
    # Test Exotel handler
    handler = ExotelStreamHandler(
        call_sid="TEST_CALL_001",
        on_transcript=on_transcript,
        on_alert=on_alert
    )
    
    handler.start()
    
    # Generate mock audio data (sine wave)
    import numpy as np
    
    def generate_mock_audio(duration_sec: float, sample_rate: int = 8000) -> bytes:
        """Generate mock audio sine wave for testing"""
        samples = int(sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, samples)
        # 440 Hz sine wave
        audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        return audio.tobytes()
    
    # Simulate incoming audio chunks
    test_phrases = [
        "Hello, this is the IRS",  # First chunk
        "Send me bitcoin immediately",  # Second chunk - should trigger alert
        "or you will be arrested",  # Third chunk
        "Thank you for your cooperation"  # Fourth chunk
    ]
    
    for i, phrase in enumerate(test_phrases):
        print(f"\n📞 Simulating chunk {i+1}: '{phrase}'")
        
        # Generate mock audio
        mock_audio = generate_mock_audio(3.0, 8000)
        
        # Process the chunk
        # In real scenario, this would be base64 encoded from Exotel
        result = handler.process_message({
            "event": "media",
            "call_sid": "TEST_CALL_001",
            "stream_sid": "stream_123",
            "media": {"payload": "mock_data"}
        })
        
        # For test, directly process the mock audio
        # This bypasses base64 decoding for testing
        handler.processor.process_chunk(mock_audio, 8000, {"test": True})
        
        time.sleep(1)
    
    # Stop handler
    handler.stop()
    
    print("\n" + "=" * 60)
    print("✅ Stream Processor Test Complete")
    print("=" * 60)
    
    # Show summary
    print("\n📊 Call Summary:")
    print(json.dumps(handler.get_summary(), indent=2))