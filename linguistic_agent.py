# linguistic_agent.py
# Linguistic Pattern Agent
# Integrated with Audio Feature Agent for family impersonation detection

import time
import os
import json
from groq import Groq
from audio_agent import AudioFeatureAgent

# ============================================
# 1. SETUP: Groq Client
# ============================================
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ============================================
# 2. PROMPT: Instructions for the LLM
# ============================================
SYSTEM_PROMPT = """
You are a fraud detection analyst. Analyze the phone call transcript below and return a JSON object with exactly these fields:

{
  "scam_likelihood": <integer 0-100>,
  "scam_type": "<string>",
  "reason_codes": ["<string>", ...],
  "summary": "<one sentence explanation>",
  "recommended_action": "<'allow', 'warn', or 'block'>"
}

Scam markers to look for:
- Urgency or time pressure
- Secrecy demands
- Impersonation of authority (bank, police, government)
- Requests for OTP, PIN, CVV, passwords, etc.
- Threats of account freeze or legal action
- Pressure to make immediate payments
- Requests to move to WhatsApp, Telegram, etc.

The transcript may contain a mix of Hindi and English (Hinglish). Understand both languages.

IMPORTANT: This transcript may be incomplete (the call is still in progress).
- If there is not enough information yet, keep scam_likelihood low (under 30).
- Only increase the score when you see clear scam markers.
- Do not guess; base your analysis only on what is explicitly said.
- A caller simply introducing themselves as from a bank is NOT enough to flag a scam.

If the transcript appears normal or incomplete, set scam_likelihood < 30 and scam_type = "none".
Do NOT include any text outside the JSON. The response must be valid JSON only.

Strict JSON Rules:
- Return ONLY the five fields: scam_likelihood, scam_type, reason_codes, summary, recommended_action.
- Do NOT add any extra fields like "confidence" or "indicators".
- "summary" MUST be a single sentence under 100 characters.
- "scam_type" MUST be one of: "bank impersonation", "police impersonation", "tech support", "courier scam", "lottery scam", "none".
- "recommended_action" MUST be exactly "allow", "warn", or "block".

If the transcript appears normal or incomplete, set scam_likelihood < 30 and scam_type = "none".
Do NOT include any text outside the JSON. The response must be valid JSON only.

If the transcript is only a few words or an incomplete sentence (e.g., "Hello, this is..."), keep scam_likelihood 0 and scam_type "none". Only flag when you see clear scam behavior.
"""

# Allowed reason codes (must match what Person 4 expects)
ALLOWED_REASON_CODES = {
    "urgency", "secrecy", "authority_impersonation",
    "sensitive_data_request", "threat", "payment_pressure",
    "reward_bait", "off_platform"
}

# Family keywords that trigger voice analysis
FAMILY_KEYWORDS = [
    "grandma", "grandpa", "grandmother", "grandfather",
    "mom", "dad", "mummy", "papa", "mother", "father",
    "uncle", "aunt", "aunty", "cousin", "brother", "sister",
    "beta", "betaa", "beti", "nana", "nani", "dada", "dadi"
]

ALLOWED_SCAM_TYPES = {
    "bank impersonation", "police impersonation", "tech support",
    "courier scam", "lottery scam", "none"
}

def normalize_reason_codes(codes: list) -> list:
    """
    Filter and normalize reason codes to only allowed values.
    Maps common variations to the canonical list.
    """
    if not codes:
        return []
    
    normalized = []
    for code in codes:
        code_lower = code.lower().replace(" ", "_").replace("-", "_")
        
        # Direct match
        if code_lower in ALLOWED_REASON_CODES:
            normalized.append(code_lower)
        # Map variations
        elif "urgent" in code_lower or "time_pressure" in code_lower:
            normalized.append("urgency")
        elif "secret" in code_lower or "don't_tell" in code_lower:
            normalized.append("secrecy")
        elif ("impersonat" in code_lower or "authority" in code_lower or 
              "bank" in code_lower or "bank_se" in code_lower):
            normalized.append("authority_impersonation")
        elif "otp" in code_lower or "pin" in code_lower or "password" in code_lower or "cvv" in code_lower:
            normalized.append("sensitive_data_request")
        elif "threat" in code_lower or "freeze" in code_lower or "legal" in code_lower or "arrest" in code_lower:
            normalized.append("threat")
        elif "payment" in code_lower or "pay" in code_lower or "transfer" in code_lower:
            normalized.append("payment_pressure")
        elif "prize" in code_lower or "won" in code_lower or "lottery" in code_lower:
            normalized.append("reward_bait")
        elif "whatsapp" in code_lower or "telegram" in code_lower or "off_platform" in code_lower:
            normalized.append("off_platform")
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for code in normalized:
        if code not in seen:
            seen.add(code)
            unique.append(code)
    return unique

def filter_result(result: dict) -> dict:
    """
    Ensure the result contains only expected fields and valid values.
    """
    allowed_fields = {"scam_likelihood", "scam_type", "reason_codes", "summary", "recommended_action"}
    
    # Remove any unexpected fields
    for key in list(result.keys()):
        if key not in allowed_fields:
            del result[key]
    
    # Ensure scam_likelihood is int between 0-100
    if "scam_likelihood" in result:
        try:
            result["scam_likelihood"] = int(result["scam_likelihood"])
            result["scam_likelihood"] = max(0, min(100, result["scam_likelihood"]))
        except (ValueError, TypeError):
            result["scam_likelihood"] = 0
    
    # Normalize scam_type
    if "scam_type" in result:
        st = result["scam_type"].lower()
        if "bank" in st:
            result["scam_type"] = "bank impersonation"
        elif "police" in st or "officer" in st:
            result["scam_type"] = "police impersonation"
        elif "tech" in st or "microsoft" in st or "support" in st:
            result["scam_type"] = "tech support"
        elif "courier" in st or "fedex" in st or "customs" in st:
            result["scam_type"] = "courier scam"
        elif "lottery" in st or "prize" in st:
            result["scam_type"] = "lottery scam"
        elif st == "none" or result["scam_likelihood"] < 30:
            result["scam_type"] = "none"
        else:
            result["scam_type"] = "bank impersonation"  # default fallback
    
    # Ensure summary is a single short sentence
    if "summary" in result:
        summary = result["summary"]
        if len(summary) > 150:
            summary = summary[:147] + "..."
        result["summary"] = summary
    
    # Normalize recommended_action
    if "recommended_action" in result:
        action = result["recommended_action"].lower()
        if action in ("allow", "warn", "block"):
            result["recommended_action"] = action
        else:
            # Infer from scam_likelihood
            score = result.get("scam_likelihood", 0)
            if score > 70:
                result["recommended_action"] = "block"
            elif score > 40:
                result["recommended_action"] = "warn"
            else:
                result["recommended_action"] = "allow"
    
    return result

# ============================================
# 3. CORE FUNCTION: Analyze Transcript
# ============================================
def analyze_transcript(transcript: str, model: str = "llama-3.1-8b-instant", audio_bytes: bytes = None) -> dict:
    words = transcript.strip().split()
    if len(words) < 5:
        return {
            "scam_likelihood": 0,
            "scam_type": "none",
            "reason_codes": [],
            "summary": "Insufficient transcript for analysis.",
            "recommended_action": "allow"
        }
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ],
            temperature=0.0,
            max_tokens=500,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        if "reason_codes" in result:
            result["reason_codes"] = normalize_reason_codes(result["reason_codes"])
        
        result = filter_result(result)
        
        # --- INTEGRATION: Check for family keywords and trigger audio analysis ---
        if audio_bytes is not None:
            transcript_lower = transcript.lower()
            if any(kw in transcript_lower for kw in FAMILY_KEYWORDS):
                try:
                    audio_agent = AudioFeatureAgent()
                    audio_result = audio_agent.analyze_chunk(
                        audio_bytes=audio_bytes,
                        call_id="batch-call",
                        stream_sid="batch-stream"
                    )
                    result["audio_analysis"] = audio_result
                    
                    # Boost scam likelihood if voice mismatch detected
                    if audio_result.get("voice_match_score", 1.0) < 0.3:
                        result["scam_likelihood"] = min(100, result["scam_likelihood"] + 20)
                        if "voice_mismatch" not in result["reason_codes"]:
                            result["reason_codes"].append("voice_mismatch")
                        if result["recommended_action"] == "allow":
                            result["recommended_action"] = "warn"
                except Exception as e:
                    print(f"Audio analysis failed: {e}")
                    result["audio_analysis"] = None
        else:
            result["audio_analysis"] = None
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}\nRaw response: {content}")
        return {
            "scam_likelihood": 0,
            "scam_type": "error",
            "reason_codes": [],
            "summary": "Analysis failed due to invalid JSON response.",
            "recommended_action": "allow",
            "audio_analysis": None
        }
    except Exception as e:
        # API failure fallback (for demo resilience)
        print(f"API error: {e}")
        if "account will be blocked" in transcript.lower():
            return {
                "scam_likelihood": 95,
                "scam_type": "bank impersonation",
                "reason_codes": ["urgency", "authority_impersonation"],
                "summary": "Scam detected (fallback mode).",
                "recommended_action": "block",
                "audio_analysis": None
            }
        else:
            return {
                "scam_likelihood": 0,
                "scam_type": "none",
                "reason_codes": [],
                "summary": "Analysis unavailable due to API error.",
                "recommended_action": "allow",
                "audio_analysis": None
            }

# ============================================
# 4. REAL-TIME CONTEXT HANDLER
# ============================================
class TranscriptAnalyzer:
    def __init__(self, max_turns=10, reference_voice_path=None):
        self.history = []
        self.max_turns = max_turns
        self.audio_agent = AudioFeatureAgent(reference_voice_path=reference_voice_path)

    def add_chunk(self, speaker: str, text: str, audio_bytes: bytes = None) -> dict:
        timestamp = time.time()
        self.history.append(f"[{timestamp:.2f}] {speaker}: {text}")
        
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]
        
        transcript = "\n".join(self.history)
        result = analyze_transcript(transcript)
        result["timestamp"] = timestamp
        
        # --- Check for family keywords and trigger audio analysis ---
        if audio_bytes is not None:
            transcript_lower = transcript.lower()
            if any(kw in transcript_lower for kw in FAMILY_KEYWORDS):
                try:
                    audio_result = self.audio_agent.analyze_chunk(
                        audio_bytes=audio_bytes,
                        call_id="stream-call",
                        stream_sid="stream-stream"
                    )
                    result["audio_analysis"] = audio_result
                    
                    # Boost scam likelihood if voice mismatch detected
                    if audio_result.get("voice_match_score", 1.0) < 0.3:
                        result["scam_likelihood"] = min(100, result["scam_likelihood"] + 20)
                        if "voice_mismatch" not in result["reason_codes"]:
                            result["reason_codes"].append("voice_mismatch")
                        if result["recommended_action"] == "allow":
                            result["recommended_action"] = "warn"
                except Exception as e:
                    print(f"Audio analysis failed: {e}")
                    result["audio_analysis"] = None
        else:
            result["audio_analysis"] = None
        
        return result

    def reset(self):
        self.history = []
