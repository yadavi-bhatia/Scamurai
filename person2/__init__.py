"""
Person 2 - Linguistic Pattern Agent
Complete scam detection system with Hindi/Hinglish support
"""

from .linguistic_agent import LinguisticAgent, DetectionResult, ScamKeywordDatabase
from .config import *
from .evidence_builder import EvidenceBuilder, EvidenceRecord
from .asr_engine import get_asr_engine, GoogleASREngine, WhisperASREngine, MockASREngine
from .stream_processor import StreamProcessor, ExotelStreamHandler, FileStreamProcessor

__version__ = "2.1.0"
__all__ = [
    "LinguisticAgent",
    "DetectionResult", 
    "ScamKeywordDatabase",
    "EvidenceBuilder",
    "EvidenceRecord",
    "get_asr_engine",
    "GoogleASREngine",
    "WhisperASREngine",
    "MockASREngine",
    "StreamProcessor",
    "ExotelStreamHandler",
    "FileStreamProcessor"
]