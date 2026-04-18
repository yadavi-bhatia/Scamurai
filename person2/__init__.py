"""
Person 2 - Linguistic Pattern Agent
Complete scam detection system with Hindi/Hinglish support
"""

from .linguistic_agent import LinguisticAgent
from .config import *
from .evidence_builder import EvidenceBuilder
from .asr_engine import get_asr_engine
from .stream_processor import StreamProcessor, ExotelStreamHandler
from .frozen_handoff import FrozenHandoffGenerator, FrozenHandoff

__version__ = "2.0.0"
__all__ = [
    "LinguisticAgent",
    "EvidenceBuilder",
    "get_asr_engine",
    "StreamProcessor",
    "ExotelStreamHandler",
    "FrozenHandoffGenerator",
    "FrozenHandoff"
]