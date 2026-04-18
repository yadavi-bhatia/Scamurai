"""
Person 2 - Speech-to-Text Engine
Multiple backends: Google (free), Whisper (better), AssemblyAI (premium)
"""

import os
import tempfile
import wave
import audioop
from typing import Optional, Dict, Any, Callable
from abc import ABC, abstractmethod
import config


class ASREngine(ABC):
    """Abstract base class for ASR engines"""
    
    @abstractmethod
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio bytes to text"""
        pass
    
    @abstractmethod
    def transcribe_file(self, file_path: str) -> str:
        """Transcribe audio file to text"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available"""
        pass


class GoogleASREngine(ASREngine):
    """
    Google Speech Recognition
    Free, no API key needed for limited use
    Supports Hindi + Indian English
    """
    
    def __init__(self, language: str = "hi-IN"):
        self.language = language
        self._available = False
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self._available = True
        except ImportError:
            print("⚠️ SpeechRecognition not installed. Run: pip install SpeechRecognition")
    
    def is_available(self) -> bool:
        return self._available
    
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        if not self._available:
            return "[ASR: SpeechRecognition not installed]"
        
        try:
            import speech_recognition as sr
            
            # Convert to WAV in memory
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                # Write WAV header
                with wave.open(f, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                temp_path = f.name
            
            # Transcribe
            with sr.AudioFile(temp_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                
                # Try with specified language first
                try:
                    text = self.recognizer.recognize_google(audio, language=self.language)
                except:
                    # Fallback to English
                    text = self.recognizer.recognize_google(audio, language="en-IN")
            
            os.unlink(temp_path)
            return text if text else "[ASR: No speech detected]"
            
        except Exception as e:
            return f"[ASR Error: {str(e)[:50]}]"
    
    def transcribe_file(self, file_path: str) -> str:
        if not self._available:
            return "[ASR: SpeechRecognition not installed]"
        
        try:
            import speech_recognition as sr
            with sr.AudioFile(file_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                
                try:
                    text = self.recognizer.recognize_google(audio, language=self.language)
                except:
                    text = self.recognizer.recognize_google(audio, language="en-IN")
            
            return text if text else "[ASR: No speech detected]"
            
        except Exception as e:
            return f"[ASR Error: {str(e)[:50]}]"


class WhisperASREngine(ASREngine):
    """
    OpenAI Whisper
    Better accuracy, supports multiple languages
    Requires more resources
    """
    
    def __init__(self, model_size: str = "tiny", language: str = "hi"):
        self.model_size = model_size
        self.language = language
        self._available = False
        self.model = None
        
        try:
            import whisper
            self.whisper = whisper
            self.model = whisper.load_model(model_size)
            self._available = True
        except ImportError:
            print("⚠️ Whisper not installed. Run: pip install openai-whisper")
    
    def is_available(self) -> bool:
        return self._available
    
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        if not self._available:
            return "[ASR: Whisper not installed]"
        
        try:
            import numpy as np
            
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            result = self.model.transcribe(audio_np, language=self.language, fp16=False)
            return result["text"].strip()
            
        except Exception as e:
            return f"[Whisper Error: {str(e)[:50]}]"
    
    def transcribe_file(self, file_path: str) -> str:
        if not self._available:
            return "[ASR: Whisper not installed]"
        
        try:
            result = self.model.transcribe(file_path, language=self.language)
            return result["text"].strip()
        except Exception as e:
            return f"[Whisper Error: {str(e)[:50]}]"


class MockASREngine(ASREngine):
    """
    Mock ASR engine for testing
    Returns predefined responses based on keywords
    """
    
    def __init__(self):
        self._available = True
    
    def is_available(self) -> bool:
        return True
    
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        # For testing, return a mock response
        # In production, you'd use real ASR
        return "Send me bitcoin immediately or you will be arrested"
    
    def transcribe_file(self, file_path: str) -> str:
        return self.transcribe(b'')


class StreamingASR:
    """
    Handles real-time streaming audio transcription
    Processes audio chunks as they arrive
    """
    
    def __init__(self, engine: ASREngine, chunk_duration: float = 3.0, sample_rate: int = 16000):
        self.engine = engine
        self.chunk_duration = chunk_duration
        self.sample_rate = sample_rate
        self.buffer = b''
        self.buffer_duration = 0.0
        self.is_final = False
    
    def process_chunk(self, audio_chunk: bytes, chunk_sample_rate: int) -> Optional[str]:
        """
        Process an incoming audio chunk
        Returns transcription when enough audio is buffered
        """
        # Resample if needed
        if chunk_sample_rate != self.sample_rate:
            audio_chunk = audioop.ratecv(audio_chunk, 2, 1, chunk_sample_rate, self.sample_rate, None)[0]
        
        # Add to buffer
        self.buffer += audio_chunk
        chunk_duration_sec = len(audio_chunk) / (self.sample_rate * 2)  # 2 bytes per sample
        self.buffer_duration += chunk_duration_sec
        
        # Process if buffer is full enough
        if self.buffer_duration >= self.chunk_duration:
            text = self.engine.transcribe(self.buffer, self.sample_rate)
            self.buffer = b''
            self.buffer_duration = 0.0
            return text
        
        return None
    
    def finalize(self) -> Optional[str]:
        """Process any remaining audio in buffer"""
        if len(self.buffer) > 0:
            return self.engine.transcribe(self.buffer, self.sample_rate)
        return None


def get_asr_engine(engine_name: str = None) -> ASREngine:
    """
    Factory function to get ASR engine
    
    Args:
        engine_name: "google", "whisper", or "mock"
    """
    if engine_name is None:
        engine_name = config.ASR_CONFIG.get("engine", "google")
    
    engines = {
        "google": GoogleASREngine,
        "whisper": WhisperASREngine,
        "mock": MockASREngine
    }
    
    engine_class = engines.get(engine_name, GoogleASREngine)
    
    if engine_name == "google":
        language = config.ASR_CONFIG.get("language", "hi-IN")
        return engine_class(language=language)
    elif engine_name == "whisper":
        language = "hi" if "hi" in config.ASR_CONFIG.get("language", "hi-IN") else "en"
        return engine_class(model_size="tiny", language=language)
    else:
        return engine_class()


# Quick test
if __name__ == "__main__":
    print("Testing ASR Engines...")
    print("-" * 40)
    
    # Test Google
    google_engine = get_asr_engine("google")
    print(f"Google ASR available: {google_engine.is_available()}")
    
    # Test Whisper
    whisper_engine = get_asr_engine("whisper")
    print(f"Whisper ASR available: {whisper_engine.is_available()}")
    
    # Test streaming
    streaming_asr = StreamingASR(google_engine, chunk_duration=3.0)
    print("\nStreaming ASR initialized")