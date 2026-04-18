"""
PERSON 2 - WAV PROCESSOR (Hours 24-36)
Process WAV files from Person 1 with all new features
"""

import os
import json
import time
import speech_recognition as sr
from datetime import datetime
from typing import Dict, Any, List, Optional
from linguistic_agent import LinguisticAgent
from deepfake_detector import DeepfakeDetector
from family_matcher import FamilyVoiceMatcher, VoiceMatchResult
from alert_generator import AlertGenerator


class WAVProcessor:
    """
    Complete WAV processor for Person 1 integration
    Includes: Transcription + Scam Detection + Deepfake + Family Match + Alerts
    """
    
    def __init__(self, watch_directory: str = "./incoming_calls"):
        self.watch_directory = watch_directory
        self.agent = LinguisticAgent("person2_processor")
        self.deepfake_detector = DeepfakeDetector()
        self.family_matcher = FamilyVoiceMatcher()
        self.alert_generator = AlertGenerator()
        
        self.processed_files: List[str] = []
        self.results_dir = "./results"
        
        os.makedirs(watch_directory, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        print("=" * 70)
        print("PERSON 2 - WAV PROCESSOR READY")
        print("=" * 70)
        print(f"Watching: {watch_directory}")
        print(f"Results: {self.results_dir}")
        print(f"Features: Transcription + Scam + Deepfake + Family Match + Alerts")
        print("=" * 70)
    
    def process_wav_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single WAV file from Person 1
        
        Returns:
            Complete analysis result with all fields for Person 3
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        print(f"\n[PROCESSING] {os.path.basename(file_path)}")
        
        # Step 1: Transcribe audio
        transcript, audio_bytes = self._transcribe_wav(file_path)
        
        if not transcript:
            return {"error": "Transcription failed", "file": file_path}
        
        # Step 2: Analyze text for scams
        text_result = self.agent.analyze(transcript)
        
        # Step 3: Deepfake detection (if audio available)
        deepfake_result = self.deepfake_detector.analyze_audio_features(audio_bytes) if audio_bytes else {}
        
        # Step 4: Family voice matching (if we have references)
        family_match = None
        if self.family_matcher.family_members:
            # In production, extract voice features from audio
            family_match = self.family_matcher.match_voice({})
        
        # Step 5: Generate alert
        handoff = self.agent.get_handoff()
        alert = self.alert_generator.generate_alert(handoff)
        
        # Step 6: Build complete result for Person 3
        result = {
            "source_file": os.path.basename(file_path),
            "timestamp": datetime.now().isoformat(),
            "transcript": transcript,
            "scam_analysis": text_result.to_dict(),
            "deepfake_analysis": deepfake_result,
            "family_match": family_match.to_dict() if family_match else None,
            "alert": alert,
            "handoff": handoff.to_dict(),
            "status": "complete"
        }
        
        # Step 7: Save result
        result_file = os.path.join(
            self.results_dir,
            f"{os.path.basename(file_path)}.result.json"
        )
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"   RISK: {text_result.risk_score:.0%} ({text_result.risk_level})")
        print(f"   SCAM TYPE: {text_result.scam_type}")
        print(f"   MONEY: {text_result.money_amount_mentioned}")
        print(f"   FAMILY IMPERSONATION: {text_result.family_impersonation}")
        print(f"   ALERT: {alert['short_message']}")
        print(f"   Saved: {result_file}")
        
        return result
    
    def _transcribe_wav(self, file_path: str) -> tuple:
        """Transcribe WAV file to text"""
        recognizer = sr.Recognizer()
        audio_bytes = None
        
        try:
            with sr.AudioFile(file_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
                
                # Get audio bytes for deepfake detection
                with open(file_path, 'rb') as f:
                    audio_bytes = f.read()
                
                # Transcribe (Hindi + English support)
                text = recognizer.recognize_google(audio, language="hi-IN")
                return text, audio_bytes
                
        except sr.UnknownValueError:
            return "[Could not understand audio]", audio_bytes
        except sr.RequestError:
            return "[Speech recognition error]", audio_bytes
        except Exception as e:
            return f"[Error: {str(e)}]", audio_bytes
    
    def add_family_reference(self, name: str, relationship: str, reference_wav: str):
        """Add a family member's voice reference"""
        transcript, audio_bytes = self._transcribe_wav(reference_wav)
        self.family_matcher.add_family_member(name, relationship, {"features": "placeholder"})
        print(f"[FAMILY] Added reference for {name} ({relationship})")
    
    def process_batch(self, file_paths: List[str]) -> List[Dict]:
        """Process multiple WAV files"""
        results = []
        for file_path in file_paths:
            result = self.process_wav_file(file_path)
            results.append(result)
        return results
    
    def start_watching(self):
        """Start watching directory for new files (simplified)"""
        print(f"\n[WATCHING] Monitoring {self.watch_directory} for new WAV files...")
        print("Press Ctrl+C to stop\n")
        
        processed = set()
        
        try:
            while True:
                for file in os.listdir(self.watch_directory):
                    if file.endswith('.wav') and file not in processed:
                        file_path = os.path.join(self.watch_directory, file)
                        self.process_wav_file(file_path)
                        processed.add(file)
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n[STOPPED] WAV processor stopped")


def main():
    """Main entry point"""
    import sys
    
    processor = WAVProcessor("./incoming_calls")
    
    if len(sys.argv) > 1:
        # Process specific file
        result = processor.process_wav_file(sys.argv[1])
        print("\n" + "=" * 70)
        print("COMPLETE RESULT FOR PERSON 3")
        print("=" * 70)
        print(json.dumps(result, indent=2))
    else:
        # Watch mode
        processor.start_watching()


if __name__ == "__main__":
    main()