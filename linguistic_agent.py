# linguistic_agent.py


import os
import json
from groq import Groq

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
"""
# Allowed reason codes (must match what Person 4 expects)
ALLOWED_REASON_CODES = {
    "urgency", "secrecy", "authority_impersonation",
    "sensitive_data_request", "threat", "payment_pressure",
    "reward_bait", "off_platform"
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
        elif "impersonat" in code_lower or "authority" in code_lower or "bank" in code_lower:
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

# ============================================
# 3. CORE FUNCTION: Analyze Transcript
# ============================================
def analyze_transcript(transcript: str, model: str = "llama-3.1-8b-instant") -> dict:
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
        
        # ===== HOUR 5-6 UPDATE: Normalize reason codes =====
        if "reason_codes" in result:
            result["reason_codes"] = normalize_reason_codes(result["reason_codes"])
        # ===================================================
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}\nRaw response: {content}")
        return {
            "scam_likelihood": 0,
            "scam_type": "error",
            "reason_codes": [],
            "summary": "Analysis failed due to invalid JSON response.",
            "recommended_action": "allow"
        }
    except Exception as e:
        return {
            "scam_likelihood": 0,
            "scam_type": "error",
            "reason_codes": [],
            "summary": f"API error: {str(e)}",
            "recommended_action": "allow"
        }


# ============================================
# 4. REAL-TIME CONTEXT HANDLER
# ============================================
class TranscriptAnalyzer:
    def __init__(self, max_turns=10):
        self.history = []
        self.max_turns = max_turns

    def add_chunk(self, speaker: str, text: str) -> dict:
        self.history.append(f"{speaker}: {text}")
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]
        
        transcript = "\n".join(self.history)
        return analyze_transcript(transcript)

    def reset(self):
        self.history = []

# ============================================
# 5. TESTING SECTION (HOUR 5-6 FOCUS)
# ============================================

def run_full_demo():
    """
    Run all prepared demo scenarios and print a judge-friendly summary.
    This is the main demo function for the hackathon presentation.
    """
    # Import demo transcripts (create this file separately)
    try:
        from demo_transcripts import DEMO_SCENARIOS
    except ImportError:
        print("Error: demo_transcripts.py not found. Using fallback test.")
        DEMO_SCENARIOS = {}
    
    print("\n" + "="*70)
    print("🛡️  DEFEND & DETECT - Linguistic Pattern Agent Demo")
    print("="*70)
    print("Person 3: Real-Time Scam Transcript Analysis\n")
    
    for key, scenario in DEMO_SCENARIOS.items():
        print(f"\n📋 SCENARIO: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print("-"*70)
        
        if "transcript" in scenario:
            # Batch analysis
            result = analyze_transcript(scenario["transcript"])
        else:
            # Streaming analysis
            analyzer = TranscriptAnalyzer(max_turns=10)
            for speaker, text in scenario["chunks"]:
                result = analyzer.add_chunk(speaker, text)
            analyzer.reset()
        
        # Determine risk emoji
        action = result.get("recommended_action", "allow")
        if action == "block":
            risk_display = "🔴 DANGEROUS"
            risk_emoji = "🔴"
        elif action == "warn":
            risk_display = "🟡 SUSPICIOUS"
            risk_emoji = "🟡"
        else:
            risk_display = "🟢 SAFE"
            risk_emoji = "🟢"
        
        # Print result in clean format
        print(f"   Result: {risk_display}")
        print(f"   Scam Likelihood: {result['scam_likelihood']}/100")
        print(f"   Scam Type: {result.get('scam_type', 'none')}")
        print(f"   Reason Codes: {', '.join(result.get('reason_codes', [])) or 'None'}")
        print(f"   Summary: {result.get('summary', 'N/A')}")
        print(f"   Recommended Action: {result.get('recommended_action', 'allow').upper()}")
        
        # Check if result matches expected (optional validation)
        expected = scenario.get("expected_risk", "")
        if expected:
            if (expected == "SAFE" and action == "allow") or \
               (expected == "SUSPICIOUS" and action == "warn") or \
               (expected == "DANGEROUS" and action == "block"):
                print(f"   ✅ Validation: Matches expected risk ({expected})")
            else:
                print(f"   ⚠️  Validation: Expected {expected}, got action '{action}'")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)

if __name__ == "__main__":
    import sys
    
    # Check if user wants full demo or quick test
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_full_demo()
    else:
        print("Running quick tests... (use --demo for full presentation)")
        print("-"*50)
        
        # Quick validation test
        test_transcript = """
        Caller: This is urgent! Your account will be blocked. Share OTP now.
        """
        result = analyze_transcript(test_transcript)
        print(f"Quick test: Risk={result['scam_likelihood']}, Action={result['recommended_action']}")
        print(f"Codes: {result['reason_codes']}")
        print("\nRun 'python linguistic_agent.py --demo' for full demo.")