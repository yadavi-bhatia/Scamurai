# audio_agent.py
"""
Audio Feature Analysis Agent (MFCC Version)
Enhanced deepfake detection heuristics + demo comparison mode.
No external API calls, 100% local using librosa + numpy.
"""

import os
import json
import time
import numpy as np
import librosa
import soundfile as sf
from dataclasses import dataclass, asdict
from typing import Optional, Tuple, List
from scipy.spatial.distance import cosine
import warnings
warnings.filterwarnings('ignore')


# ============================================
# HELPER: JSON serialization for numpy types
# ============================================
def convert_to_json_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj


# ============================================
# 1. DATA STRUCTURE
# ============================================
@dataclass
class AudioAnalysisResult:
    call_id: str
    stream_sid: str
    timestamp: float
    
    tone_label: str
    accent_label: str
    pace_label: str
    urgency_score: float
    
    voice_match_score: float
    deepfake_risk_score: float
    
    signal_quality_score: float
    confidence_score: float
    
    notes: str
    final_audio_risk_label: str


# ============================================
# 2. MFCC VOICE SIMILARITY
# ============================================
def extract_mfcc_voiceprint(audio: np.ndarray, sr: int = 16000) -> np.ndarray:
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    mfcc_delta = librosa.feature.delta(mfccs)
    mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
    features = np.vstack([mfccs, mfcc_delta, mfcc_delta2])
    voiceprint = np.mean(features, axis=1)
    norm = np.linalg.norm(voiceprint)
    if norm > 0:
        voiceprint = voiceprint / norm
    return voiceprint


def load_reference_voiceprint(audio_path: str) -> np.ndarray:
    audio, sr = librosa.load(audio_path, sr=16000)
    return extract_mfcc_voiceprint(audio, sr)


def compute_voice_similarity(audio: np.ndarray, reference_voiceprint: np.ndarray, sr: int = 16000) -> float:
    try:
        if len(audio) < sr * 0.5:
            return 0.0
        voiceprint = extract_mfcc_voiceprint(audio, sr)
        similarity = 1 - cosine(reference_voiceprint, voiceprint)
        return float(max(0.0, min(1.0, similarity)))
    except Exception as e:
        print(f"Voice similarity error: {e}")
        return 0.0


# ============================================
# 3. AUDIO PREPROCESSING
# ============================================
def preprocess_audio(audio_data: bytes, sample_rate: int = 16000) -> Tuple[np.ndarray, float]:
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    rms = np.sqrt(np.mean(audio_np**2))
    quality = min(1.0, rms * 5)
    if rms < 0.01:
        quality *= 0.3
    if rms > 0.95:
        quality *= 0.7
    return audio_np, float(quality)


# ============================================
# 4. ACOUSTIC FEATURE EXTRACTION
# ============================================
def extract_acoustic_features(audio: np.ndarray, sr: int = 16000) -> dict:
    features = {}
    
    # Pitch
    pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
    pitch_values = pitches[pitches > 0]
    if len(pitch_values) > 0:
        mean_pitch = np.mean(pitch_values)
        pitch_std = np.std(pitch_values)
        features['mean_pitch'] = float(mean_pitch)
        features['pitch_variation'] = float(pitch_std / (mean_pitch + 1e-6))
    else:
        features['mean_pitch'] = 0.0
        features['pitch_variation'] = 0.0
    
    # Energy
    rms = librosa.feature.rms(y=audio)[0]
    mean_energy = float(np.mean(rms))
    energy_std = float(np.std(rms))
    features['mean_energy'] = mean_energy
    features['energy_variation'] = float(energy_std / (mean_energy + 1e-6))
    
    # Spectral flatness (key deepfake indicator)
    spec_flat = librosa.feature.spectral_flatness(y=audio)[0]
    features['spectral_flatness'] = float(np.mean(spec_flat))
    
    # Tempo
    tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
    if hasattr(tempo, 'item'):
        tempo = tempo.item()
    features['tempo'] = float(tempo)
    
    # Zero-crossing rate
    zcr = librosa.feature.zero_crossing_rate(audio)[0]
    features['zcr_mean'] = float(np.mean(zcr))
    
    return features


def classify_tone(features: dict) -> str:
    pitch_var = features.get('pitch_variation', 0)
    energy_var = features.get('energy_variation', 0)
    mean_pitch = features.get('mean_pitch', 0)
    if pitch_var > 0.3 and energy_var > 0.4:
        return "urgent"
    elif pitch_var > 0.25:
        return "aggressive"
    elif energy_var < 0.1 and pitch_var < 0.15:
        return "calm"
    elif mean_pitch > 200:
        return "nervous"
    else:
        return "neutral"


def classify_pace(features: dict) -> str:
    tempo = features.get('tempo', 120)
    if tempo < 80:
        return "slow"
    elif tempo < 140:
        return "normal"
    elif tempo < 180:
        return "fast"
    else:
        return "erratic"


def calculate_urgency_score(features: dict, tone: str, pace: str) -> float:
    score = 0.0
    if pace == "fast":
        score += 0.3
    elif pace == "erratic":
        score += 0.4
    elif pace == "normal":
        score += 0.1
    if tone == "urgent":
        score += 0.4
    elif tone == "aggressive":
        score += 0.3
    elif tone == "nervous":
        score += 0.2
    if features.get('pitch_variation', 0) > 0.25:
        score += 0.2
    return min(1.0, score)


# ============================================
# 5. ENHANCED DEEPFAKE DETECTION
# ============================================
def detect_deepfake_risk(features: dict, voice_match: float) -> float:
    """
    Enhanced heuristic deepfake risk score.
    Synthetic voices often have:
    - Unnaturally consistent pitch (low variation)
    - Perfect tempo (~120 BPM)
    - High spectral flatness (lack of harmonic structure)
    - Unusual zero-crossing rate
    """
    risk = 0.0
    explanations = []
    
    pitch_var = features.get('pitch_variation', 0)
    tempo = features.get('tempo', 0)
    zcr = features.get('zcr_mean', 0)
    spec_flat = features.get('spectral_flatness', 0)
    
    # 1. Flat pitch (robotic)
    if pitch_var < 0.05:
        risk += 0.35
        explanations.append("flat pitch")
    elif pitch_var < 0.10:
        risk += 0.15
        explanations.append("low pitch variation")
        
    # 2. Perfect TTS tempo
    if 115 < tempo < 125:
        risk += 0.25
        explanations.append("perfect TTS tempo")
        
    # 3. High spectral flatness (noise-like, lacks harmonics)
    if spec_flat > 0.5:
        risk += 0.30
        explanations.append("high spectral flatness")
    elif spec_flat > 0.3:
        risk += 0.15
        explanations.append("elevated spectral flatness")
        
    # 4. Zero-crossing rate extremes
    if zcr < 0.03 or zcr > 0.45:
        risk += 0.20
        explanations.append("unusual ZCR")
        
    # 5. Voice match is high but acoustic flags suspicious → possible voice clone
    if voice_match > 0.8 and risk > 0.3:
        risk += 0.20
        explanations.append("high match + acoustic anomalies")
        
    # Cap at 1.0
    risk = min(1.0, risk)
    
    return risk


# ============================================
# 6. ACCENT CONSISTENCY
# ============================================
def classify_accent(features: dict, previous_features: Optional[dict] = None) -> str:
    if previous_features is None:
        return "unknown"
    pitch_diff = abs(features.get('mean_pitch', 0) - previous_features.get('mean_pitch', 0))
    if pitch_diff > 50:
        return "inconsistent"
    return "consistent"


# ============================================
# 7. MAIN AGENT CLASS
# ============================================
class AudioFeatureAgent:
    def __init__(self, reference_voice_path: Optional[str] = None):
        self.reference_voiceprint = None
        if reference_voice_path and os.path.exists(reference_voice_path):
            self.reference_voiceprint = load_reference_voiceprint(reference_voice_path)
        self.previous_features = None
        
    def analyze_chunk(self, 
                     audio_bytes: bytes,
                     call_id: str,
                     stream_sid: str,
                     timestamp: Optional[float] = None) -> dict:
        if timestamp is None:
            timestamp = time.time()
            
        audio_np, quality = preprocess_audio(audio_bytes)
        
        if quality < 0.1:
            result = AudioAnalysisResult(
                call_id=call_id,
                stream_sid=stream_sid,
                timestamp=timestamp,
                tone_label="unknown",
                accent_label="unknown",
                pace_label="unknown",
                urgency_score=0.0,
                voice_match_score=0.0,
                deepfake_risk_score=0.0,
                signal_quality_score=quality,
                confidence_score=0.1,
                notes="Audio quality too low for analysis",
                final_audio_risk_label="low"
            )
            return convert_to_json_serializable(asdict(result))
            
        features = extract_acoustic_features(audio_np)
        tone = classify_tone(features)
        pace = classify_pace(features)
        urgency = calculate_urgency_score(features, tone, pace)
        accent = classify_accent(features, self.previous_features)
        self.previous_features = features
        
        voice_match = 0.0
        if self.reference_voiceprint is not None:
            voice_match = compute_voice_similarity(audio_np, self.reference_voiceprint)
            
        deepfake_risk = detect_deepfake_risk(features, voice_match)
        confidence = quality * 0.6 + (1 - deepfake_risk) * 0.4
        
        if voice_match < 0.3 and self.reference_voiceprint is not None:
            risk_label = "high"
        elif deepfake_risk > 0.6 or urgency > 0.7:
            risk_label = "medium"
        else:
            risk_label = "low"
            
        result = AudioAnalysisResult(
            call_id=call_id,
            stream_sid=stream_sid,
            timestamp=timestamp,
            tone_label=tone,
            accent_label=accent,
            pace_label=pace,
            urgency_score=round(urgency, 3),
            voice_match_score=round(voice_match, 3),
            deepfake_risk_score=round(deepfake_risk, 3),
            signal_quality_score=round(quality, 3),
            confidence_score=round(confidence, 3),
            notes=f"Tone: {tone}, Pace: {pace}",
            final_audio_risk_label=risk_label
        )
        
        return convert_to_json_serializable(asdict(result))