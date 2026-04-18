#!/usr/bin/env python3
"""
PERSON 2 - Linguistic Pattern Agent
Detects scam language in transcripts
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class ScamCategories:
    """Define all scam marker categories"""
    
    PAYMENT = {
        "name": "payment_request",
        "weight": 0.45,
        "keywords": [
            "bitcoin", "btc", "crypto", "ethereum", "gift card", "giftcard",
            "google play", "itunes card", "amazon card", "western union",
            "moneygram", "wire transfer", "send money", "transfer funds",
            "cash app", "venmo", "paypal", "zelle", "apple pay"
        ]
    }
    
    IDENTITY = {
        "name": "identity_theft",
        "weight": 0.40,
        "keywords": [
            "social security", "ssn", "date of birth", "dob",
            "bank account", "account number", "routing number",
            "credit card", "debit card", "cvv", "pin", "otp",
            "password", "mother maiden", "driver license"
        ]
    }
    
    THREAT = {
        "name": "threat",
        "weight": 0.35,
        "keywords": [
            "arrest", "warrant", "jail", "prison", "police", "fbi",
            "lawsuit", "court", "judge", "freeze", "suspend",
            "terminate", "close account", "fine", "penalty"
        ]
    }
    
    URGENCY = {
        "name": "urgency",
        "weight": 0.25,
        "keywords": [
            "immediately", "right now", "don't hang up", "urgent",
            "asap", "act now", "quickly", "hurry", "deadline",
            "final warning", "last chance", "limited time"
        ]
    }
    
    AUTHORITY = {
        "name": "fake_authority",
        "weight": 0.20,
        "keywords": [
            "irs", "internal revenue service", "social security administration",
            "fbi", "police department", "fraud department", "security team",
            "government", "federal", "bank", "microsoft", "amazon", "paypal"
        ]
    }
    
    SCAM_PHRASES = {
        "name": "scam_phrases",
        "weight": 0.15,
        "keywords": [
            "your account has been compromised",
            "suspicious activity detected",
            "verify your identity",
            "confirm your information",
            "security alert",
            "fraud alert",
            "you've won",
            "tech support"
        ]
    }
    
    @classmethod
    def get_all_categories(cls) -> List[Dict]:
        return [cls.PAYMENT, cls.IDENTITY, cls.THREAT, cls.URGENCY, cls.AUTHORITY, cls.SCAM_PHRASES]
    
    @classmethod
    def get_all_keywords(cls) -> List[str]:
        keywords = []
        for cat in cls.get_all_categories():
            keywords.extend(cat["keywords"])
        return keywords


class LinguisticAgent:
    """Person 2: Linguistic Pattern Agent"""
    
    def __init__(self):
        self.scam_categories = ScamCategories.get_all_categories()
        self.total_risk = 0.0
        self.detection_history = []
        self.compiled_patterns = self._compile_patterns()
        print("✅ Linguistic Agent initialized")
        print(f"   Monitoring {len(self.scam_categories)} categories")
        print(f"   Total keywords: {len(ScamCategories.get_all_keywords())}")
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for all categories"""
        patterns = {}
        for cat in self.scam_categories:
            keywords = [re.escape(kw) for kw in cat["keywords"]]
            pattern_str = r'\b(?:' + '|'.join(keywords) + r')\b'
            patterns[cat["name"]] = re.compile(pattern_str, re.IGNORECASE)
        return patterns
    
    def analyze_transcript(self, text: str) -> Dict[str, Any]:
        """Analyze transcript text for scam indicators"""
        if not text or len(text.strip()) < 3:
            return self._empty_result("Insufficient text")
        
        detected_cats = []
        detected_kws = []
        total_risk = 0.0
        
        for cat in self.scam_categories:
            pattern = self.compiled_patterns.get(cat["name"])
            if pattern:
                matches = pattern.findall(text)
                if matches:
                    detected_cats.append(cat["name"])
                    detected_kws.extend(matches)
                    total_risk += cat["weight"] * min(len(matches), 3) / 3
        
        total_risk = min(1.0, total_risk)
        self.total_risk = min(1.0, self.total_risk * 0.7 + total_risk * 0.3)
        
        risk_level, action, verdict = self._get_risk_level(total_risk)
        scam_type = self._get_scam_type(detected_cats)
        explanation = self._get_explanation(detected_cats, detected_kws)
        reason_codes = self._get_reason_codes(detected_cats)
        
        self.detection_history.append({
            "timestamp": datetime.now().isoformat(),
            "text": text[:200],
            "risk": total_risk,
            "keywords": detected_kws[:5]
        })
        
        return {
            "transcript": text[:500],
            "detected_keywords": detected_kws[:10],
            "detected_categories": detected_cats,
            "keyword_count": len(detected_kws),
            "category_count": len(detected_cats),
            "turn_risk": round(total_risk, 3),
            "cumulative_risk": round(self.total_risk, 3),
            "risk_level": risk_level,
            "action_required": action,
            "verdict": verdict,
            "scam_type": scam_type,
            "explanation": explanation,
            "reason_codes": reason_codes,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_risk_level(self, risk: float) -> Tuple[str, str, str]:
        """Determine risk level based on score"""
        if risk >= 0.6:
            return ("🔴 CRITICAL", "INTERVENE IMMEDIATELY", "SCAM CONFIRMED")
        elif risk >= 0.4:
            return ("🟠 HIGH", "ESCALATE NOW", "SCAM LIKELY")
        elif risk >= 0.2:
            return ("🟡 MEDIUM", "MONITOR CAREFULLY", "SUSPICIOUS")
        elif risk > 0:
            return ("🔵 LOW", "REVIEW LATER", "CAUTION ADVISED")
        else:
            return ("🟢 NONE", "NO ACTION", "SAFE")
    
    def _get_scam_type(self, categories: List[str]) -> str:
        """Determine scam type from detected categories"""
        type_mapping = {
            "payment_request": "payment_scam",
            "identity_theft": "identity_theft_scam",
            "threat": "threat_scam",
            "fake_authority": "impersonation_scam",
            "urgency": "pressure_tactic",
            "scam_phrases": "generic_scam"
        }
        
        for cat in ["payment_request", "identity_theft", "threat", "fake_authority", "urgency", "scam_phrases"]:
            if cat in categories:
                return type_mapping.get(cat, "unknown_scam")
        
        return "none"
    
    def _get_explanation(self, categories: List[str], keywords: List[str]) -> str:
        """Generate human-readable explanation"""
        if not categories:
            return "No scam indicators detected"
        
        parts = []
        if "payment_request" in categories:
            parts.append("requested payment")
        if "identity_theft" in categories:
            parts.append("asked for personal info")
        if "threat" in categories:
            parts.append("used threats")
        if "fake_authority" in categories:
            parts.append("impersonated authority")
        if "urgency" in categories:
            parts.append("created urgency")
        if "scam_phrases" in categories:
            parts.append("used scam phrases")
        
        if parts:
            return f"Suspicious: {'; '.join(parts[:3])}"
        return "General suspicious patterns detected"
    
    def _get_reason_codes(self, categories: List[str]) -> List[str]:
        """Get standardized reason codes"""
        mapping = {
            "payment_request": "R01_PAYMENT_REQUEST",
            "identity_theft": "R02_IDENTITY_THEFT",
            "threat": "R03_THREAT",
            "fake_authority": "R04_FAKE_AUTHORITY",
            "urgency": "R05_URGENCY",
            "scam_phrases": "R06_SCAM_PHRASE"
        }
        return [mapping[cat] for cat in categories if cat in mapping]
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty result when no text"""
        return {
            "transcript": "",
            "detected_keywords": [],
            "detected_categories": [],
            "keyword_count": 0,
            "category_count": 0,
            "turn_risk": 0.0,
            "cumulative_risk": round(self.total_risk, 3),
            "risk_level": "⚪ EMPTY",
            "action_required": "NONE",
            "verdict": "NO INPUT",
            "scam_type": "none",
            "explanation": f"Error: {reason}",
            "reason_codes": [],
            "error": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_partial_transcript(self, text: str, is_final: bool = False) -> Dict[str, Any]:
        """Handle partial/incomplete transcripts from live ASR"""
        if not text or len(text.strip()) < 3:
            return {
                "transcript": text,
                "is_final": is_final,
                "status": "insufficient_text",
                "turn_risk": 0.0,
                "verdict": "WAITING_FOR_MORE",
                "timestamp": datetime.now().isoformat()
            }
        
        result = self.analyze_transcript(text)
        result["is_final"] = is_final
        result["status"] = "analyzed"
        
        if not is_final:
            result["turn_risk"] = round(result["turn_risk"] * 0.8, 3)
            result["note"] = "Partial transcript - confidence reduced"
        
        return result
    
    def reset_session(self):
        """Reset for new call session"""
        self.total_risk = 0.0
        self.detection_history = []
        print("🔄 Session reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent": "Person 2 - Linguistic Agent",
            "status": "ready",
            "categories_monitored": len(self.scam_categories),
            "total_keywords": len(ScamCategories.get_all_keywords()),
            "detections_this_session": len(self.detection_history),
            "current_cumulative_risk": round(self.total_risk, 3)
        }


if __name__ == "__main__":
    print("=" * 60)
    print("PERSON 2 - LINGUISTIC AGENT")
    print("=" * 60)
    
    agent = LinguisticAgent()
    
    test_text = "Send me $500 in bitcoin immediately or you will be arrested"
    result = agent.analyze_transcript(test_text)
    
    print("\n📊 SAMPLE OUTPUT:")
    print(json.dumps(result, indent=2))