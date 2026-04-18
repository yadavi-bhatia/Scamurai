"""
PERSON 2 - WORKING SINGLE FILE
Copy this entire file, run it, it works.
"""

import json
import re
import time
import wave
import threading
import queue
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Try to import speech recognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Install: pip install SpeechRecognition")

# Try to import pyaudio for microphone
try:
    import pyaudio
    PA_AVAILABLE = True
except ImportError:
    PA_AVAILABLE = False


# ============================================================
# SCAM KEYWORDS (English only)
# ============================================================

SCAM_KEYWORDS = {
    "payment": {
        "keywords": ["bitcoin", "gift card", "western union", "send money", "wire transfer", "paypal"],
        "weight": 0.45
    },
    "identity": {
        "keywords": ["otp", "social security", "bank account", "password", "credit card", "aadhaar"],
        "weight": 0.40
    },
    "threat": {
        "keywords": ["arrest", "warrant", "jail", "police", "lawsuit", "freeze", "irs"],
        "weight": 0.35
    },
    "urgency": {
        "keywords": ["immediately", "right now", "urgent", "don't hang up", "asap", "act now"],
        "weight": 0.25
    },
    "authority": {
        "keywords": ["irs", "bank", "police", "microsoft", "government", "rbi"],
        "weight": 0.18
    }
}

# Money pattern
MONEY_PATTERN = re.compile(r'\$\d+(?:,\d+)*|\d+\s*(?:dollars|USD)', re.IGNORECASE)


# ============================================================
# MAIN AGENT CLASS
# ============================================================

class Person2Agent:
    def __init__(self):
        self.turn_count = 0
        self.history = []
        
        # Compile regex patterns
        self.patterns = {}
        for cat, data in SCAM_KEYWORDS.items():
            escaped = [re.escape(kw) for kw in data["keywords"]]
            self.patterns[cat] = re.compile(r'\b(?:' + '|'.join(escaped) + r')\b', re.IGNORECASE)
        
        print("Person 2 Agent Ready")
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text and return scam detection results"""
        if not text or len(text.strip()) < 3:
            return self._empty_result()
        
        detected_cats = []
        detected_kws = []
        total_risk = 0.0
        
        # Check each category
        for category, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_cats.append(category)
                detected_kws.extend(matches[:3])
                total_risk += SCAM_KEYWORDS[category]["weight"] * min(len(matches), 2) / 2
        
        # Check for money
        if MONEY_PATTERN.search(text):
            total_risk += 0.10
            detected_kws.append("[MONEY]")
        
        total_risk = min(1.0, total_risk)
        
        # Determine risk level
        if total_risk >= 0.70:
            risk_level = "CRITICAL"
            action = "BLOCK CALL"
            verdict = "SCAM CONFIRMED"
        elif total_risk >= 0.50:
            risk_level = "HIGH"
            action = "ESCALATE"
            verdict = "SCAM LIKELY"
        elif total_risk >= 0.30:
            risk_level = "MEDIUM"
            action = "MONITOR"
            verdict = "SUSPICIOUS"
        elif total_risk >= 0.10:
            risk_level = "LOW"
            action = "REVIEW"
            verdict = "CAUTION"
        else:
            risk_level = "NONE"
            action = "NONE"
            verdict = "SAFE"
        
        # Determine scam type
        scam_type = "none"
        for cat in ["payment", "identity", "threat", "authority"]:
            if cat in detected_cats:
                scam_type = cat + "_scam"
                break
        
        # Generate explanation
        if not detected_cats:
            explanation = "No scam indicators detected"
        else:
            exp_map = {
                "payment": "Payment requested",
                "identity": "Personal info requested",
                "threat": "Threats used",
                "urgency": "Urgency created",
                "authority": "Fake authority"
            }
            exp_parts = [exp_map.get(c, c) for c in detected_cats[:2]]
            explanation = "; ".join(exp_parts)
            if detected_kws:
                explanation += f" (keyword: {detected_kws[0]})"
        
        result = {
            "risk_score": round(total_risk, 3),
            "risk_level": risk_level,
            "scam_type": scam_type,
            "detected_keywords": detected_kws[:5],
            "detected_categories": detected_cats,
            "explanation": explanation,
            "recommended_action": action,
            "verdict": verdict,
            "transcript": text[:200],
            "timestamp": datetime.now().isoformat()
        }
        
        self.history.append(result)
        return result
    
    def _empty_result(self) -> Dict[str, Any]:
        return {
            "risk_score": 0.0,
            "risk_level": "NONE",
            "scam_type": "none",
            "detected_keywords": [],
            "detected_categories": [],
            "explanation": "Insufficient text",
            "recommended_action": "NONE",
            "verdict": "NO INPUT",
            "transcript": "",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# TRANSCRIPTION FUNCTION
# ============================================================

def transcribe_audio_file(file_path: str) -> str:
    """Transcribe a WAV file to text"""
    if not SR_AVAILABLE:
        return ""
    
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="en-US")
            return text
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""


def transcribe_microphone(duration: int = 5) -> str:
    """Record from microphone and transcribe"""
    if not SR_AVAILABLE or not PA_AVAILABLE:
        print("Microphone not available")
        return ""
    
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print(f"Listening for {duration} seconds...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            text = recognizer.recognize_google(audio, language="en-US")
            return text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print(f"Error: {e}")
        return ""


# ============================================================
# DEMO FUNCTIONS
# ============================================================

def demo_text():
    """Demo with text input"""
    print("\n" + "=" * 60)
    print("PERSON 2 - TEXT ANALYSIS DEMO")
    print("=" * 60)
    
    agent = Person2Agent()
    
    test_texts = [
        "Send me $5000 in bitcoin immediately or you will be arrested",
        "Please verify your OTP and social security number",
        "Hello, I'm calling to confirm my appointment"
    ]
    
    for text in test_texts:
        print(f"\nInput: {text}")
        result = agent.analyze(text)
        print(f"   Risk: {result['risk_score']:.0%} ({result['risk_level']})")
        print(f"   Type: {result['scam_type']}")
        print(f"   Keywords: {result['detected_keywords']}")
        print(f"   Action: {result['recommended_action']}")


def demo_file(file_path: str):
    """Demo with audio file"""
    print("\n" + "=" * 60)
    print("PERSON 2 - AUDIO FILE ANALYSIS")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"\nFile: {file_path}")
    
    # Transcribe
    text = transcribe_audio_file(file_path)
    
    if not text:
        print("Could not transcribe audio")
        return
    
    print(f"Transcript: {text}")
    
    # Analyze
    agent = Person2Agent()
    result = agent.analyze(text)
    
    print(f"\nRESULTS:")
    print(f"   Risk Score: {result['risk_score']:.0%}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Scam Type: {result['scam_type']}")
    print(f"   Keywords: {', '.join(result['detected_keywords'])}")
    print(f"   Action: {result['recommended_action']}")


def demo_microphone():
    """Demo with live microphone"""
    print("\n" + "=" * 60)
    print("PERSON 2 - MICROPHONE DEMO")
    print("=" * 60)
    
    if not SR_AVAILABLE or not PA_AVAILABLE:
        print("Microphone not available. Install: pip install SpeechRecognition pyaudio")
        return
    
    agent = Person2Agent()
    
    print("\nSay something (you have 5 seconds)...")
    text = transcribe_microphone(duration=5)
    
    if not text:
        print("No speech detected")
        return
    
    print(f"\nYou said: {text}")
    
    result = agent.analyze(text)
    
    print(f"\nRESULTS:")
    print(f"   Risk Score: {result['risk_score']:.0%}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Scam Type: {result['scam_type']}")
    print(f"   Keywords: {', '.join(result['detected_keywords'])}")
    print(f"   Action: {result['recommended_action']}")


# ============================================================
# SIMPLE GUI (Tkinter)
# ============================================================

def run_gui():
    """Simple GUI for testing"""
    try:
        import tkinter as tk
        from tkinter import scrolledtext, messagebox
    except ImportError:
        print("Tkinter not available")
        return
    
    root = tk.Tk()
    root.title("Person 2 - Scam Detection")
    root.geometry("800x600")
    root.configure(bg='#1e1e1e')
    
    agent = Person2Agent()
    
    # Title
    title = tk.Label(root, text="Scam Detection System", font=("Arial", 18, "bold"), fg="#00ff00", bg="#1e1e1e")
    title.pack(pady=10)
    
    # Input label
    input_label = tk.Label(root, text="Enter text to analyze:", font=("Arial", 12), fg="white", bg="#1e1e1e")
    input_label.pack(anchor=tk.W, padx=20, pady=(20,5))
    
    # Text input
    text_input = scrolledtext.ScrolledText(root, height=5, font=("Arial", 11), bg="#2d2d2d", fg="white")
    text_input.pack(fill=tk.X, padx=20, pady=5)
    
    # Button frame
    button_frame = tk.Frame(root, bg="#1e1e1e")
    button_frame.pack(pady=10)
    
    def analyze():
        text = text_input.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text")
            return
        
        result = agent.analyze(text)
        
        # Clear and display results
        result_text.delete(1.0, tk.END)
        
        result_text.insert(tk.END, "=" * 50 + "\n")
        result_text.insert(tk.END, "ANALYSIS RESULTS\n")
        result_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Risk with color
        if result['risk_score'] >= 0.5:
            result_text.insert(tk.END, f"RISK SCORE: {result['risk_score']:.0%} (HIGH)\n", "red")
        elif result['risk_score'] >= 0.3:
            result_text.insert(tk.END, f"RISK SCORE: {result['risk_score']:.0%} (MEDIUM)\n", "yellow")
        else:
            result_text.insert(tk.END, f"RISK SCORE: {result['risk_score']:.0%} (LOW)\n", "green")
        
        result_text.insert(tk.END, f"RISK LEVEL: {result['risk_level']}\n")
        result_text.insert(tk.END, f"SCAM TYPE: {result['scam_type']}\n")
        result_text.insert(tk.END, f"KEYWORDS: {', '.join(result['detected_keywords'])}\n")
        result_text.insert(tk.END, f"ACTION: {result['recommended_action']}\n\n")
        result_text.insert(tk.END, f"EXPLANATION: {result['explanation']}\n")
        
        # Configure colors
        result_text.tag_config("red", foreground="#ff4444")
        result_text.tag_config("yellow", foreground="#ffaa44")
        result_text.tag_config("green", foreground="#44ff44")
    
    def clear():
        text_input.delete(1.0, tk.END)
        result_text.delete(1.0, tk.END)
    
    def load_example():
        example = "Send me $5000 in bitcoin immediately or you will be arrested"
        text_input.delete(1.0, tk.END)
        text_input.insert(1.0, example)
        analyze()
    
    analyze_btn = tk.Button(button_frame, text="Analyze", command=analyze, font=("Arial", 12), bg="#4444ff", fg="white", padx=20, pady=5)
    analyze_btn.pack(side=tk.LEFT, padx=5)
    
    clear_btn = tk.Button(button_frame, text="Clear", command=clear, font=("Arial", 12), bg="#555555", fg="white", padx=20, pady=5)
    clear_btn.pack(side=tk.LEFT, padx=5)
    
    example_btn = tk.Button(button_frame, text="Load Example", command=load_example, font=("Arial", 12), bg="#33aa33", fg="white", padx=20, pady=5)
    example_btn.pack(side=tk.LEFT, padx=5)
    
    # Results label
    results_label = tk.Label(root, text="Results:", font=("Arial", 12), fg="white", bg="#1e1e1e")
    results_label.pack(anchor=tk.W, padx=20, pady=(20,5))
    
    # Results display
    result_text = scrolledtext.ScrolledText(root, height=12, font=("Arial", 11), bg="#2d2d2d", fg="white")
    result_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
    
    # Footer
    footer = tk.Label(root, text="Enter any text to check if it contains scam indicators", font=("Arial", 9), fg="#888888", bg="#1e1e1e")
    footer.pack(pady=10)
    
    root.mainloop()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            demo_file(sys.argv[2])
        elif sys.argv[1] == "--mic":
            demo_microphone()
        elif sys.argv[1] == "--gui":
            run_gui()
        else:
            print("Usage:")
            print("  python person2_working.py           # Text demo")
            print("  python person2_working.py --gui     # GUI mode")
            print("  python person2_working.py --mic     # Microphone mode")
            print("  python person2_working.py --file <audio.wav>")
    else:
        demo_text()