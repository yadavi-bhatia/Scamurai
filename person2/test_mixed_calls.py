"""
Hour 16: Validate scam classification on mixed calls
Tests realistic mixed-content calls (scam + normal conversation)
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linguistic_agent import LinguisticAgent


# Mixed call scenarios (scam mixed with normal conversation)
MIXED_CALL_SCENARIOS = {
    "scam_embedded_in_normal": {
        "name": "Scam Hidden in Normal Call",
        "description": "Scammer starts normal, then shifts to scam",
        "chunks": [
            "Hello, how are you today?",
            "I'm calling from your bank's customer service.",
            "Just checking if everything is okay with your account.",
            "Actually, there's been some suspicious activity.",
            "Please verify your OTP to secure your account.",
            "Don't worry, it's just a routine check."
        ],
        "expected_risk": "HIGH",
        "expected_categories": ["identity_theft", "fake_authority"]
    },
    
    "victim_confused": {
        "name": "Confused Victim (Mixed Signals)",
        "description": "Victim gives mixed responses, scammer persists",
        "chunks": [
            "Caller: Your Aadhaar has been misused.",
            "Victim: Really? I don't think so.",
            "Caller: Yes sir, it's serious. You could be arrested.",
            "Victim: That sounds scary but I need to verify.",
            "Caller: No time! Send OTP immediately!",
            "Victim: Let me call my son first.",
            "Caller: Don't tell anyone! This is confidential!"
        ],
        "expected_risk": "HIGH",
        "expected_categories": ["threat", "urgency", "identity_theft"]
    },
    
    "partial_scam": {
        "name": "Partial Scam (Incomplete Information)",
        "description": "Scammer starts but victim hangs up midway",
        "chunks": [
            "This is IRS. You owe back taxes.",
            "Pay immediately or face legal action.",
            "We accept gift cards and bitcoin.",
            "[Victim hangs up]"
        ],
        "expected_risk": "MEDIUM",
        "expected_categories": ["payment_request", "threat", "fake_authority"]
    },
    
    "normal_with_scam_mention": {
        "name": "Normal Call Mentioning Scam",
        "description": "Victim mentions they received a scam call",
        "chunks": [
            "Friend: Hey, did you get that scam call yesterday?",
            "Victim: Yeah, someone pretending to be from the bank.",
            "Friend: They asked for OTP right?",
            "Victim: Yes, but I didn't share it.",
            "Friend: Good! Never share OTP with anyone."
        ],
        "expected_risk": "LOW",  # Not a scam, just discussing scams
        "expected_categories": []  # Should not trigger scam detection
    },
    
    "hinglish_mixed": {
        "name": "Hinglish Mixed Call",
        "description": "Mixed Hindi-English scam call",
        "chunks": [
            "Caller: Hello, main bank se bol raha hoon.",
            "Caller: Aapka account mein kuch problem hai.",
            "Victim: Kya problem hai?",
            "Caller: KYC pending hai. Jaldi karo.",
            "Caller: OTP batao warna account band.",
            "Victim: Mujhe check karna padega.",
            "Caller: Time nahi hai! Abhi batao!"
        ],
        "expected_risk": "HIGH",
        "expected_categories": ["fake_authority", "identity_theft", "urgency"]
    }
}


class MixedCallValidator:
    """Validate classification on mixed calls"""
    
    def __init__(self):
        self.agent = LinguisticAgent("mixed_call_test")
        self.results = []
    
    def validate_scenario(self, name: str, data: dict) -> dict:
        """Validate a single mixed call scenario"""
        chunks = data.get("chunks", [])
        expected_risk = data.get("expected_risk", "UNKNOWN")
        expected_categories = data.get("expected_categories", [])
        
        # Process each chunk and track cumulative risk
        cumulative_risk = 0.0
        chunk_results = []
        all_detected_categories = set()
        
        for i, chunk_text in enumerate(chunks):
            # Clean chunk (remove speaker labels for analysis)
            clean_text = chunk_text.replace("Caller:", "").replace("Victim:", "").replace("Friend:", "").strip()
            
            result = self.agent.analyze_transcript(clean_text)
            
            # Update cumulative risk with decay
            cumulative_risk = min(1.0, cumulative_risk * 0.8 + result.risk_score * 0.2)
            
            for cat in result.detected_categories:
                all_detected_categories.add(cat)
            
            chunk_results.append({
                "chunk": i + 1,
                "text": chunk_text[:60],
                "risk": result.risk_score,
                "categories": result.detected_categories,
                "keywords": result.detected_keywords[:3]
            })
        
        # Determine final risk level
        if cumulative_risk >= 0.6:
            actual_risk = "HIGH"
        elif cumulative_risk >= 0.3:
            actual_risk = "MEDIUM"
        elif cumulative_risk >= 0.1:
            actual_risk = "LOW"
        else:
            actual_risk = "SAFE"
        
        # Check category match
        expected_set = set(expected_categories)
        detected_set = all_detected_categories
        category_match = len(detected_set & expected_set) / max(1, len(expected_set)) if expected_set else len(detected_set) == 0
        
        passed = (actual_risk == expected_risk) and (category_match >= 0.5)
        
        return {
            "scenario": name,
            "description": data.get("description", ""),
            "expected_risk": expected_risk,
            "actual_risk": actual_risk,
            "cumulative_risk": round(cumulative_risk, 3),
            "detected_categories": list(detected_set),
            "expected_categories": expected_categories,
            "category_match": category_match,
            "passed": passed,
            "chunk_results": chunk_results
        }
    
    def run_validation(self):
        """Run all mixed call validations"""
        print("\n" + "=" * 80)
        print("📞 HOUR 16: Mixed Call Validation")
        print("Testing scam classification on mixed/nuanced calls")
        print("=" * 80)
        
        for name, data in MIXED_CALL_SCENARIOS.items():
            result = self.validate_scenario(name, data)
            self.results.append(result)
            
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"\n{status} | {result['scenario']}")
            print(f"   {result['description']}")
            print(f"   Expected: {result['expected_risk']} | Actual: {result['actual_risk']}")
            print(f"   Cumulative Risk: {result['cumulative_risk']:.0%}")
            print(f"   Detected Categories: {result['detected_categories']}")
            print(f"   Category Match: {result['category_match']}")
            
            # Show critical chunks
            high_risk_chunks = [c for c in result["chunk_results"] if c["risk"] >= 0.3]
            if high_risk_chunks:
                print(f"   ⚠️ Alert triggered at chunk {high_risk_chunks[0]['chunk']}")
        
        # Summary
        passed = sum(1 for r in self.results if r["passed"])
        print("\n" + "-" * 80)
        print(f"📊 Mixed Call Validation Summary:")
        print(f"   Total: {len(self.results)} scenarios")
        print(f"   Passed: {passed}")
        print(f"   Failed: {len(self.results) - passed}")
        print(f"   Accuracy: {(passed/len(self.results))*100:.1f}%")
        
        return self.results


if __name__ == "__main__":
    validator = MixedCallValidator()
    validator.run_validation()