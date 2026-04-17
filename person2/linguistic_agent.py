"""
Linguistic Pattern Agent for Scam Call Detection
Detects scam indicators in conversation transcripts including:
- Stylometric features (hesitation, urgency, repetition)
- Known scam phrases
- Contradictions in caller statements
- Combined linguistic risk score
"""

import json
import re
from typing import Dict, List, Any, Optional

# Try to import whisper, but provide fallback for testing without it
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: whisper not installed. Using mock transcription for testing.")


class LinguisticAgent:
    """Linguistic analysis agent for detecting scam patterns in phone calls"""
    
    def __init__(self, use_mock_asr: bool = False):
        """
        Initialize the linguistic agent
        
        Args:
            use_mock_asr: If True, use mock transcriptions for testing without audio files
        """
        # Scam phrase dictionary (high-risk indicators)
        self.scam_phrases = [
            "gift card", "bitcoin", "ethereum", "crypto", "western union",
            "moneygram", "wire transfer", "social security", "ssn",
            "do not tell anyone", "don't hang up", "stay on the line",
            "irs", "tax fraud", "arrest warrant", "bail money", "police coming",
            "itunes card", "google play card", "paypal verification",
            "amazon card", "target card", "walmart card"
        ]
        
        # Hesitation markers (human speech indicators)
        self.hesitations = [
            "um", "uh", "like", "you know", "let me see", "actually", 
            "well", "hmm", "ah", "sort of", "kind of", "i mean"
        ]
        
        # Politeness markers
        self.polite_words = ["please", "thank you", "thanks", "apologize", "sorry", "appreciate"]
        self.demand_words = ["must", "immediately", "right now", "or else", "warning", "required"]
        
        # Urgency markers
        self.urgency_markers = [
            "immediately", "right now", "asap", "urgent", "don't hang up",
            "quickly", "now", "or else", "warning", "arrest", "jail",
            "within", "today", "one hour", "as soon as"
        ]
        
        # Slot patterns for contradiction detection
        self.slot_patterns = {
            "caller_company": r"(visa|mastercard|american express|discover|chase|bank of america|wells fargo|citi|citibank|irs|social security administration|microsoft|apple|amazon|paypal)",
            "currency_type": r"(dollars|bitcoin|ethereum|crypto|gift card|itunes card|google play card|amazon card|wire transfer|money order)",
            "action_required": r"(buy|transfer|send|verify|confirm|pay|withdraw|deposit|convert)",
            "threat_type": r"(arrest|jail|suspend|close|freeze|deactivate|terminate)"
        }
        
        # State storage
        self.slot_memory: Dict[str, str] = {}
        self.full_transcript: List[Dict] = []
        self.use_mock_asr = use_mock_asr
        
        # Load ASR model if available
        self.asr_model = None
        if WHISPER_AVAILABLE and not use_mock_asr:
            try:
                self.asr_model = whisper.load_model("tiny")
                print("✅ Whisper ASR model loaded")
            except Exception as e:
                print(f"⚠️ Could not load whisper model: {e}")
                self.use_mock_asr = True
    
    def transcribe_audio(self, audio_file_path: str) -> List[Dict]:
        """
        Convert audio file to text using Whisper
        
        Args:
            audio_file_path: Path to audio file (WAV, MP3, etc.)
            
        Returns:
            List of transcript segments with timestamps
        """
        if self.use_mock_asr or not self.asr_model:
            return self._mock_transcribe(audio_file_path)
        
        try:
            result = self.asr_model.transcribe(audio_file_path)
            
            segments = []
            for seg in result["segments"]:
                segments.append({
                    "time": round(seg["start"], 1),
                    "text": seg["text"].strip(),
                    "confidence": getattr(seg, "confidence", 0.8)
                })
            
            self.full_transcript = segments
            return segments
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return self._mock_transcribe(audio_file_path)
    
    def _mock_transcribe(self, audio_file_path: str) -> List[Dict]:
        """
        Mock transcription for testing without audio files
        Returns predefined transcripts based on filename patterns
        """
        filename = audio_file_path.lower()
        
        if "scam" in filename or "fraud" in filename:
            # Simulated scam call transcript
            mock_segments = [
                {"time": 0.0, "text": "Hello? This is Jessica from Visa fraud department.", "confidence": 0.85},
                {"time": 5.2, "text": "Someone just tried to purchase $500 in gift cards.", "confidence": 0.82},
                {"time": 10.5, "text": "Do not hang up. This is urgent.", "confidence": 0.88},
                {"time": 14.0, "text": "I need you to go to the store and buy Bitcoin immediately.", "confidence": 0.79},
                {"time": 19.0, "text": "Do not tell anyone what you're doing.", "confidence": 0.86},
                {"time": 23.0, "text": "Your social security number has been compromised.", "confidence": 0.84}
            ]
        elif "human" in filename or "normal" in filename:
            # Simulated normal human call
            mock_segments = [
                {"time": 0.0, "text": "Hi, um, I'm calling about my account.", "confidence": 0.88},
                {"time": 4.5, "text": "I think there's a charge I don't recognize.", "confidence": 0.85},
                {"time": 9.0, "text": "Let me see... it was for like $49.99.", "confidence": 0.82},
                {"time": 14.0, "text": "Actually, could you help me understand what that is?", "confidence": 0.87},
                {"time": 19.0, "text": "Thank you so much for your help.", "confidence": 0.90}
            ]
        else:
            # Default mock transcript
            mock_segments = [
                {"time": 0.0, "text": "Hello? I need help with my account.", "confidence": 0.85},
                {"time": 5.0, "text": "Can you verify some information for me?", "confidence": 0.83}
            ]
        
        self.full_transcript = mock_segments
        return mock_segments
    
    def extract_stylometric_features(self) -> Dict[str, Any]:
        """
        Calculate stylometric features:
        - Average words per utterance
        - Hesitation rate
        - Repetition flag
        - Politeness score
        - Urgency score
        
        Returns:
            Dictionary of stylometric features
        """
        if not self.full_transcript:
            return self._empty_stylometric()
        
        all_text = " ".join([seg["text"] for seg in self.full_transcript])
        utterances = [seg["text"] for seg in self.full_transcript if seg["text"].strip()]
        
        if not utterances:
            return self._empty_stylometric()
        
        # Words per utterance
        word_counts = [len(utt.split()) for utt in utterances]
        avg_words = sum(word_counts) / len(word_counts)
        
        # Hesitation markers
        hesitation_count = 0
        all_text_lower = all_text.lower()
        for h in self.hesitations:
            hesitation_count += len(re.findall(r'\b' + re.escape(h) + r'\b', all_text_lower))
        hesitation_rate = hesitation_count / len(utterances)
        
        # Repetition detection (same exact phrase)
        repetition_flag = False
        seen_phrases = set()
        for utt in utterances:
            utt_lower = utt.lower()
            if len(utt_lower) > 15 and utt_lower in seen_phrases:
                repetition_flag = True
                break
            seen_phrases.add(utt_lower)
        
        # Politeness score
        politeness = 0
        for word in self.polite_words:
            politeness += len(re.findall(r'\b' + re.escape(word) + r'\b', all_text_lower))
        for word in self.demand_words:
            politeness -= len(re.findall(r'\b' + re.escape(word) + r'\b', all_text_lower))
        politeness_norm = max(-1, min(1, politeness / 5))
        
        # Urgency score
        urgency_count = 0
        for word in self.urgency_markers:
            urgency_count += len(re.findall(r'\b' + re.escape(word) + r'\b', all_text_lower))
        urgency_score = min(1.0, urgency_count / 4)
        
        return {
            "avg_words_per_utterance": round(avg_words, 1),
            "hesitation_rate": round(hesitation_rate, 3),
            "repetition_flag": repetition_flag,
            "politeness_score": round(politeness_norm, 2),
            "urgency_score": round(urgency_score, 2),
            "total_utterances": len(utterances),
            "total_words": sum(word_counts)
        }
    
    def _empty_stylometric(self) -> Dict[str, Any]:
        """Return empty stylometric features"""
        return {
            "avg_words_per_utterance": 0,
            "hesitation_rate": 0,
            "repetition_flag": False,
            "politeness_score": 0,
            "urgency_score": 0,
            "total_utterances": 0,
            "total_words": 0
        }
    
    def detect_scam_phrases(self) -> Dict[str, Any]:
        """
        Detect known scam phrases in transcript
        
        Returns:
            Dictionary with scam phrase counts and scores
        """
        if not self.full_transcript:
            return {
                "scam_phrase_count": 0,
                "unique_scam_phrases": [],
                "time_decayed_score": 0,
                "scam_density": 0
            }
        
        all_text = " ".join([seg["text"] for seg in self.full_transcript]).lower()
        
        # Find all scam phrases
        found_phrases = []
        for phrase in self.scam_phrases:
            if phrase in all_text:
                found_phrases.append(phrase)
        
        unique_phrases = list(set(found_phrases))
        
        # Time decay: recent segments count more
        decayed_score = 0
        total_weight = 0
        for idx, seg in enumerate(self.full_transcript):
            seg_text = seg["text"].lower()
            # Recent segments get higher weight
            weight = 1.0 / (len(self.full_transcript) - idx + 1)
            total_weight += weight
            for phrase in self.scam_phrases:
                if phrase in seg_text:
                    decayed_score += weight
                    break  # Count once per segment
        
        decayed_score = min(1.0, decayed_score / total_weight if total_weight > 0 else 0)
        
        # Scam density (phrases per 100 words)
        total_words = sum([len(seg["text"].split()) for seg in self.full_transcript])
        scam_density = len(found_phrases) / max(1, total_words / 100)
        scam_density = min(1.0, scam_density / 5)  # Normalize: 5 phrases per 100 words = 1.0
        
        return {
            "scam_phrase_count": len(found_phrases),
            "unique_scam_phrases": unique_phrases,
            "time_decayed_score": round(decayed_score, 3),
            "scam_density": round(scam_density, 3)
        }
    
    def detect_contradictions(self) -> Dict[str, Any]:
        """
        Detect contradictions in caller statements using slot memory
        
        Returns:
            Dictionary with contradiction detection results
        """
        if not self.full_transcript:
            return {
                "contradictions_detected": False,
                "contradiction_count": 0,
                "contradiction_details": []
            }
        
        contradictions = []
        
        for seg in self.full_transcript:
            text = seg["text"].lower()
            
            for slot, pattern in self.slot_patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    match_clean = match.lower().strip()
                    if slot in self.slot_memory:
                        if self.slot_memory[slot] != match_clean:
                            contradictions.append({
                                "slot": slot,
                                "previous": self.slot_memory[slot],
                                "new": match_clean,
                                "time": seg["time"]
                            })
                    # Update memory (keep most recent)
                    self.slot_memory[slot] = match_clean
        
        return {
            "contradictions_detected": len(contradictions) > 0,
            "contradiction_count": len(contradictions),
            "contradiction_details": contradictions[:5]  # First 5 only
        }
    
    def compute_linguistic_risk(self, stylometric: Dict, scam: Dict, contradiction: Dict) -> Dict[str, Any]:
        """
        Combine all signals into final linguistic risk score
        
        Args:
            stylometric: Output from extract_stylometric_features()
            scam: Output from detect_scam_phrases()
            contradiction: Output from detect_contradictions()
            
        Returns:
            Final risk assessment
        """
        # Extract components
        urgency = stylometric.get("urgency_score", 0)
        scam_density = scam.get("scam_density", 0)
        scam_time_decayed = scam.get("time_decayed_score", 0)
        contradiction_score = 0.25 if contradiction.get("contradictions_detected") else 0
        hesitation = stylometric.get("hesitation_rate", 0)
        politeness = stylometric.get("politeness_score", 0)
        
        # Low hesitation is suspicious (AI/scripted)
        low_hesitation_score = 1 - min(1.0, hesitation * 2)  # Scale: 0 hesitation = 1.0
        
        # Very high politeness can be suspicious (scammers often overly polite)
        politeness_suspicion = max(0, politeness)  # Positive politeness adds suspicion
        
        # Weighted combination
        risk = (
            (urgency * 0.25) +
            (scam_time_decayed * 0.35) +
            (contradiction_score * 0.20) +
            (low_hesitation_score * 0.12) +
            (politeness_suspicion * 0.08)
        )
        
        # Clamp to 0-1 range
        risk = max(0.0, min(1.0, risk))
        
        # Human speech indicators (counterweight for final interpretation)
        human_indicators = []
        if hesitation > 0.2:
            human_indicators.append("hesitations_present")
        if stylometric.get("avg_words_per_utterance", 0) < 10:
            human_indicators.append("short_utterances")
        if stylometric.get("repetition_flag", False):
            human_indicators.append("natural_repetition")
        if politeness < 0:
            human_indicators.append("normal_politeness")
        
        # Determine urgency level text
        if urgency > 0.6:
            urgency_level = "high"
        elif urgency > 0.3:
            urgency_level = "medium"
        else:
            urgency_level = "low"
        
        # Caller type hint
        if risk > 0.7:
            caller_type_hint = "likely_scam"
        elif risk < 0.3:
            caller_type_hint = "likely_human"
        else:
            caller_type_hint = "uncertain"
        
        # Generate notes
        notes = self._generate_notes(risk, scam, contradiction, human_indicators)
        
        return {
            "linguistic_risk_score": round(risk, 3),
            "urgency_level": urgency_level,
            "caller_type_hint": caller_type_hint,
            "human_speech_indicators": human_indicators,
            "notes": notes,
            "component_scores": {
                "urgency_contribution": round(urgency * 0.25, 3),
                "scam_contribution": round(scam_time_decayed * 0.35, 3),
                "contradiction_contribution": round(contradiction_score, 3),
                "low_hesitation_contribution": round(low_hesitation_score * 0.12, 3),
                "politeness_contribution": round(politeness_suspicion * 0.08, 3)
            }
        }
    
    def _generate_notes(self, risk: float, scam: Dict, contradiction: Dict, human_indicators: List) -> str:
        """Generate human-readable notes about the analysis"""
        notes_parts = []
        
        if scam.get("scam_phrase_count", 0) > 2:
            notes_parts.append(f"{scam['scam_phrase_count']} scam phrases detected")
        elif scam.get("scam_phrase_count", 0) > 0:
            notes_parts.append(f"{scam['scam_phrase_count']} potential scam phrase(s)")
        
        if contradiction.get("contradictions_detected"):
            notes_parts.append(f"{contradiction['contradiction_count']} contradiction(s) detected")
        
        if risk > 0.7:
            notes_parts.append("high linguistic risk")
        elif risk < 0.3:
            notes_parts.append("low linguistic risk")
        
        if human_indicators:
            notes_parts.append("human speech patterns present")
        
        if not notes_parts:
            notes_parts.append("no clear indicators")
        
        return " | ".join(notes_parts)
    
    def analyze_call(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Main entry point - performs complete linguistic analysis on a call
        
        Args:
            audio_file_path: Path to audio file (or string identifier for mock mode)
            
        Returns:
            Complete linguistic analysis result
        """
        # Reset state for new call
        self.slot_memory = {}
        
        # Step 1: Transcribe
        transcript = self.transcribe_audio(audio_file_path)
        
        if not transcript:
            return {
                "error": "Transcription failed",
                "linguistic_risk_score": 0.5,
                "caller_type_hint": "uncertain",
                "notes": "Could not transcribe audio"
            }
        
        # Step 2: Extract stylometric features
        stylometric = self.extract_stylometric_features()
        
        # Step 3: Detect scam phrases
        scam = self.detect_scam_phrases()
        
        # Step 4: Detect contradictions
        contradiction = self.detect_contradictions()
        
        # Step 5: Compute final risk
        final = self.compute_linguistic_risk(stylometric, scam, contradiction)
        
        # Step 6: Return full result
        return {
            "linguistic_risk_score": final["linguistic_risk_score"],
            "scam_phrase_count": scam["scam_phrase_count"],
            "unique_scam_phrases": scam["unique_scam_phrases"][:5],
            "urgency_level": final["urgency_level"],
            "contradictions_detected": contradiction["contradictions_detected"],
            "human_speech_indicators": final["human_speech_indicators"],
            "notes": final["notes"],
            "caller_type_hint": final["caller_type_hint"],
            "stylometric": stylometric,
            "component_scores": final["component_scores"]
        }
    
    def analyze_text_transcript(self, transcript_text: str) -> Dict[str, Any]:
        """
        Analyze a pre-existing text transcript (for testing without audio)
        
        Args:
            transcript_text: Full transcript as a string
            
        Returns:
            Complete linguistic analysis result
        """
        # Reset state
        self.slot_memory = {}
        
        # Create mock segments from text
        sentences = re.split(r'[.!?]+', transcript_text)
        self.full_transcript = []
        for idx, sentence in enumerate(sentences):
            if sentence.strip():
                self.full_transcript.append({
                    "time": idx * 3.0,
                    "text": sentence.strip(),
                    "confidence": 0.9
                })
        
        # Run analysis
        stylometric = self.extract_stylometric_features()
        scam = self.detect_scam_phrases()
        contradiction = self.detect_contradictions()
        final = self.compute_linguistic_risk(stylometric, scam, contradiction)
        
        return {
            "linguistic_risk_score": final["linguistic_risk_score"],
            "scam_phrase_count": scam["scam_phrase_count"],
            "unique_scam_phrases": scam["unique_scam_phrases"][:5],
            "urgency_level": final["urgency_level"],
            "contradictions_detected": contradiction["contradictions_detected"],
            "human_speech_indicators": final["human_speech_indicators"],
            "notes": final["notes"],
            "caller_type_hint": final["caller_type_hint"]
        }


# ============== Command-line interface ==============
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Linguistic Agent for Scam Detection")
    parser.add_argument("audio_file", nargs="?", help="Path to audio file to analyze")
    parser.add_argument("--text", help="Analyze a text transcript instead of audio")
    parser.add_argument("--mock", action="store_true", help="Use mock ASR mode")
    
    args = parser.parse_args()
    
    agent = LinguisticAgent(use_mock_asr=args.mock)
    
    if args.text:
        result = agent.analyze_text_transcript(args.text)
    elif args.audio_file:
        result = agent.analyze_call(args.audio_file)
    else:
        # Demo mode - run on test scenarios
        print("=" * 60)
        print("Linguistic Agent - Demo Mode")
        print("=" * 60)
        
        test_scenarios = [
            ("scam_call", "scam"),
            ("human_call", "human"),
            ("mixed_call", "mixed")
        ]
        
        for name, scenario in test_scenarios:
            print(f"\n📞 Testing: {scenario.upper()} CALL")
            print("-" * 40)
            result = agent.analyze_call(f"mock_{scenario}.wav")
            print(f"Risk Score: {result['linguistic_risk_score']}")
            print(f"Caller Type: {result['caller_type_hint']}")
            print(f"Scam Phrases: {result['scam_phrase_count']}")
            print(f"Contradictions: {result['contradictions_detected']}")
            print(f"Human Indicators: {result['human_speech_indicators']}")
            print(f"Notes: {result['notes']}")
    
    if result and "error" not in result:
        print("\n" + "=" * 60)
        print("FULL RESULT (JSON):")
        print("=" * 60)
        print(json.dumps(result, indent=2))