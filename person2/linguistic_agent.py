"""
Person 2 - Linguistic Pattern Agent
Production-ready scam detection with Hindi/Hinglish support
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import config


class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class DetectionResult:
    """Structured detection result"""
    turn_id: str
    session_id: str
    timestamp: str
    transcript: str
    detected_keywords: List[str]
    detected_categories: List[str]
    risk_score: float
    risk_level: str
    scam_type: str
    explanation: str
    reason_codes: List[str]
    evidence_hash: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class ScamKeywordDatabase:
    """Manages the scam keyword database with Hindi/Hinglish support"""
    
    VERSION = "2.1"
    
    # Complete keyword database by category - English + Hindi + Hinglish
    KEYWORDS = {
        "payment_request": [
            # English
            "bitcoin", "btc", "crypto", "gift card", "giftcard",
            "google play", "itunes card", "amazon card", 
            "western union", "moneygram", "wire transfer",
            "send money", "transfer funds", "cash app", "venmo", "paypal",
            # Hindi/Hinglish
            "paisa bhejo", "paisa bhej", "rupay", "rupee", "payment karo",
            "transfer karo", "money bhejo", "amount do", "pay karo",
            "gift card lelo", "bitcoin lelo", "crypto lelo"
        ],
        "identity_theft": [
            # English
            "social security", "ssn", "date of birth", "dob",
            "bank account", "account number", "routing number",
            "credit card", "debit card", "cvv", "pin", "otp",
            "password", "passcode", "mother maiden", "driver license",
            # Hindi/Hinglish
            "aadhaar", "pan card", "pan number", "bank details",
            "account details", "personal information", "private info",
            "otp batao", "pin batao", "password batao", "verify karo",
            "confirm karo", "identity verify", "kYC complete"
        ],
        "threat": [
            # English
            "arrest", "warrant", "jail", "prison", "police", "fbi",
            "lawsuit", "court", "judge", "freeze", "suspend",
            "terminate", "close account", "fine", "penalty",
            # Hindi/Hinglish
            "arrest hoga", "jail hoga", "police aayegi", "case file",
            "legal action", "court case", "fine lagega", "penalty lagega",
            "account freeze", "account band", "suspend karenge",
            "pakda denge", "catch karenge", "problem hogi"
        ],
        "urgency": [
            # English
            "immediately", "right now", "don't hang up", "urgent",
            "asap", "act now", "quickly", "hurry", "deadline",
            "final warning", "last chance", "limited time",
            # Hindi/Hinglish
            "jaldi karo", "abhi karo", "turant", "immediate karo",
            "phone mat rakho", "call mat karo", "urgent hai",
            "time kam hai", "last chance hai", "final warning hai",
            "dekhlo", "sambhal lo", "warning hai"
        ],
        "fake_authority": [
            # English
            "irs", "internal revenue service", "social security administration",
            "fbi", "police department", "fraud department", "security team",
            "government", "federal", "bank", "microsoft", "amazon", "paypal",
            # Hindi/Hinglish
            "income tax", "IT department", "CBI", "ED", "cyber crime",
            "police station", "thana", "court", "judge sahab",
            "bank manager", "reserve bank", "RBI", "government official",
            "sarkari department", "kendra sarkar", "authority"
        ],
        "scam_phrases": [
            # English
            "your account has been compromised",
            "suspicious activity detected", "verify your identity",
            "confirm your information", "security alert", "fraud alert",
            "you've won", "tech support", "virus detected",
            # Hindi/Hinglish
            "aapka account compromised hai",
            "suspicious activity payi gayi",
            "identity verify karein", "KYC complete karein",
            "account update karein", "information confirm karein",
            "aap jeet gaye", "lottery lagi hai", "prize money milega",
            "tech support bol raha hu", "virus aa gaya hai"
        ]
    }
    
    # Phrase patterns (regex) for complex detection - Indian context
    PATTERNS = {
        "money_amount": r'₹?\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:rupees|Rs\.?|INR|lakh|crore|thousand|hundred|hazaar|lakhs|crores|पैसे|रुपये))?',
        "phone_number": r'(\+91|0)?[6-9]\d{9}\b',
        "aadhaar_pan": r'\b\d{4}\s?\d{4}\s?\d{4}\b|\b[A-Z]{5}\d{4}[A-Z]{1}\b',
        "urgency_phrase": r'(?:urgent|immediate|jaldi|asap|right now|abhi|don\'?t hang up|phone mat rakho|call mat karo|turant|dekhlo|sambhal lo)',
        "threat_phrase": r'(?:arrest|warrant|jail|prison|lawsuit|court|judge|police|case|legal|kanooni|pakda denge|jail bhej denge|case file karenge|problem hogi)'
    }
    
    @classmethod
    def get_all_keywords(cls) -> List[str]:
        all_kw = []
        for keywords in cls.KEYWORDS.values():
            all_kw.extend(keywords)
        return all_kw
    
    @classmethod
    def get_keywords_by_category(cls, category: str) -> List[str]:
        return cls.KEYWORDS.get(category, [])
    
    @classmethod
    def get_version(cls) -> str:
        return cls.VERSION


class LinguisticAgent:
    """
    Production-ready Linguistic Pattern Agent with Hindi/Hinglish support
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.keyword_db = ScamKeywordDatabase()
        self.total_risk = 0.0
        self.turn_count = 0
        self.detection_history: List[DetectionResult] = []
        self.compiled_patterns = self._compile_patterns()
        
        print(f"🎯 Linguistic Agent initialized")
        print(f"   Session: {self.session_id}")
        print(f"   Keywords: {len(self.keyword_db.get_all_keywords())}")
        print(f"   Categories: {len(config.SCAM_CATEGORIES)}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        from uuid import uuid4
        return str(uuid4())[:8]
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for all categories"""
        patterns = {}
        for category, keywords in self.keyword_db.KEYWORDS.items():
            escaped = [re.escape(kw) for kw in keywords]
            pattern_str = r'\b(?:' + '|'.join(escaped) + r')\b'
            patterns[category] = re.compile(pattern_str, re.IGNORECASE)
        
        # Add phrase patterns
        for name, pattern_str in self.keyword_db.PATTERNS.items():
            patterns[name] = re.compile(pattern_str, re.IGNORECASE)
        
        return patterns
    
    def analyze_transcript(self, text: str, speaker: str = "caller") -> DetectionResult:
        """
        Analyze transcript and return structured result with evidence
        """
        self.turn_count += 1
        turn_id = f"{self.session_id}_{self.turn_count:04d}"
        
        if not text or len(text.strip()) < 3:
            return self._create_empty_result(turn_id, text, speaker)
        
        detected_cats = []
        detected_kws = []
        total_risk = 0.0
        
        # Category-based detection
        for category, pattern in self.compiled_patterns.items():
            if category in self.keyword_db.KEYWORDS:
                matches = pattern.findall(text)
                if matches:
                    detected_cats.append(category)
                    detected_kws.extend(matches)
                    weight = config.SCAM_CATEGORIES.get(category, {}).get("weight", 0.15)
                    # Each keyword adds weight, but cap at 3 per category
                    total_risk += weight * min(len(matches), 3) / 3
        
        # Pattern-based detection (adds bonus risk)
        pattern_bonus = 0
        if 'money_amount' in self.compiled_patterns:
            if self.compiled_patterns['money_amount'].search(text):
                pattern_bonus += 0.08
                detected_kws.append("[MONEY_AMOUNT]")
        
        if 'phone_number' in self.compiled_patterns:
            if self.compiled_patterns['phone_number'].search(text):
                pattern_bonus += 0.08
                detected_kws.append("[PHONE_NUMBER]")
        
        if 'aadhaar_pan' in self.compiled_patterns:
            if self.compiled_patterns['aadhaar_pan'].search(text):
                pattern_bonus += 0.12  # Higher because Aadhaar/PAN is sensitive
                detected_kws.append("[AADHAAR_PAN]")
        
        total_risk += pattern_bonus
        total_risk = min(1.0, total_risk)
        
        # Update cumulative risk with decay
        self.total_risk = min(1.0, self.total_risk * 0.7 + total_risk * 0.3)
        
        # Determine risk level
        risk_level, action, verdict = self._get_risk_level(total_risk)
        scam_type = self._get_scam_type(detected_cats)
        explanation = self._get_explanation(detected_cats, detected_kws, total_risk)
        reason_codes = self._get_reason_codes(detected_cats)
        
        # Generate evidence hash
        evidence_string = f"{turn_id}|{self.session_id}|{text}|{total_risk}|{datetime.now().isoformat()}"
        evidence_hash = hashlib.sha256(evidence_string.encode()).hexdigest()[:16]
        
        result = DetectionResult(
            turn_id=turn_id,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            transcript=text[:500],
            detected_keywords=detected_kws[:10],
            detected_categories=detected_cats,
            risk_score=round(total_risk, 3),
            risk_level=risk_level,
            scam_type=scam_type,
            explanation=explanation,
            reason_codes=reason_codes,
            evidence_hash=evidence_hash
        )
        
        self.detection_history.append(result)
        
        # Auto-save if high risk
        if total_risk >= config.RISK_THRESHOLDS.get("high", 0.5):
            self._save_evidence(result)
        
        return result
    
    def _get_risk_level(self, risk: float) -> Tuple[str, str, str]:
        """Determine risk level with action recommendations"""
        thresholds = config.RISK_THRESHOLDS
        if risk >= thresholds.get("critical", 0.70):
            return ("CRITICAL", "IMMEDIATE_INTERVENTION", "SCAM CONFIRMED")
        elif risk >= thresholds.get("high", 0.50):
            return ("HIGH", "ESCALATE_NOW", "SCAM LIKELY")
        elif risk >= thresholds.get("medium", 0.30):
            return ("MEDIUM", "MONITOR_CAREFULLY", "SUSPICIOUS")
        elif risk >= thresholds.get("low", 0.10):
            return ("LOW", "REVIEW_LATER", "CAUTION")
        else:
            return ("NONE", "NO_ACTION", "SAFE")
    
    def _get_scam_type(self, categories: List[str]) -> str:
        """Determine primary scam type"""
        type_mapping = {
            "payment_request": "payment_scam",
            "identity_theft": "identity_theft_scam",
            "threat": "government_impersonation",
            "fake_authority": "authority_impersonation",
            "urgency": "pressure_tactic"
        }
        
        for cat in ["payment_request", "identity_theft", "threat", "fake_authority"]:
            if cat in categories:
                return type_mapping.get(cat, "unknown")
        
        if "urgency" in categories:
            return "urgency_scam"
        
        return "unknown" if categories else "none"
    
    def _get_explanation(self, categories: List[str], keywords: List[str], risk: float) -> str:
        """Generate forensic-quality explanation"""
        if not categories:
            return "No scam indicators detected in this turn"
        
        explanations = {
            "payment_request": "💰 Payment or money transfer requested",
            "identity_theft": "🆔 Personal/identifying information requested",
            "threat": "⚠️ Threatening or intimidating language used",
            "fake_authority": "👮 Impersonation of authority figure detected",
            "urgency": "⏰ Artificial urgency or pressure tactics detected",
            "scam_phrases": "📝 Known scam phrase patterns detected"
        }
        
        detected_explanations = [explanations[cat] for cat in categories if cat in explanations]
        
        if detected_explanations:
            base = "; ".join(detected_explanations[:2])
            if keywords:
                return f"{base} | Keywords: {', '.join(keywords[:3])}"
            return base
        
        return "Suspicious patterns detected"
    
    def _get_reason_codes(self, categories: List[str]) -> List[str]:
        """Return standardized reason codes"""
        code_map = {
            "payment_request": "R01",
            "identity_theft": "R02", 
            "threat": "R03",
            "fake_authority": "R04",
            "urgency": "R05",
            "scam_phrases": "R06"
        }
        return [code_map[cat] for cat in categories if cat in code_map]
    
    def _create_empty_result(self, turn_id: str, text: str, speaker: str) -> DetectionResult:
        """Create empty result for invalid input"""
        return DetectionResult(
            turn_id=turn_id,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            transcript=text,
            detected_keywords=[],
            detected_categories=[],
            risk_score=0.0,
            risk_level="NONE",
            scam_type="none",
            explanation="Insufficient text for analysis",
            reason_codes=[],
            evidence_hash=""
        )
    
    def _save_evidence(self, result: DetectionResult):
        """Save high-risk evidence to disk"""
        import os
        os.makedirs(config.EVIDENCE_CONFIG.get("output_dir", "./evidence"), exist_ok=True)
        
        evidence_file = f"./evidence/{result.turn_id}.json"
        with open(evidence_file, 'w') as f:
            f.write(result.to_json())
        print(f"💾 Evidence saved: {evidence_file}")
    
    def analyze_stream(self, text_chunks: List[Dict]) -> List[DetectionResult]:
        """Analyze a stream of text chunks (real-time)"""
        results = []
        alert_triggered = False
        
        for chunk in text_chunks:
            text = chunk.get('text', '')
            speaker = chunk.get('speaker', 'caller')
            is_final = chunk.get('is_final', False)
            
            result = self.analyze_transcript(text, speaker)
            results.append(result)
            
            if result.risk_score >= config.RISK_THRESHOLDS.get("high", 0.5) and not alert_triggered:
                alert_triggered = True
                result.explanation += " [⚠️ ALERT_TRIGGERED]"
            
            if not is_final:
                result.risk_score = round(result.risk_score * 0.85, 3)
        
        return results
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get complete session summary with verdict"""
        if not self.detection_history:
            return {"error": "No data for this session"}
        
        max_risk = max([r.risk_score for r in self.detection_history])
        all_keywords = []
        all_categories = []
        
        for r in self.detection_history:
            all_keywords.extend(r.detected_keywords)
            all_categories.extend(r.detected_categories)
        
        unique_keywords = list(set(all_keywords))
        unique_categories = list(set(all_categories))
        
        # Final verdict
        if max_risk >= config.RISK_THRESHOLDS.get("critical", 0.70):
            final_verdict = "🔴 SCAM_CONFIRMED"
            final_action = "BLOCK_CALL_IMMEDIATELY"
        elif max_risk >= config.RISK_THRESHOLDS.get("high", 0.50):
            final_verdict = "🟠 HIGH_RISK_SCAM_LIKELY"
            final_action = "ESCALATE_TO_HUMAN"
        elif max_risk >= config.RISK_THRESHOLDS.get("medium", 0.30):
            final_verdict = "🟡 SUSPICIOUS_MONITOR"
            final_action = "FLAG_FOR_REVIEW"
        else:
            final_verdict = "🟢 LOW_RISK_SAFE"
            final_action = "NO_ACTION"
        
        return {
            "session_id": self.session_id,
            "total_turns": len(self.detection_history),
            "max_risk_score": round(max_risk, 3),
            "final_verdict": final_verdict,
            "recommended_action": final_action,
            "unique_keywords_detected": unique_keywords[:20],
            "scam_categories_detected": unique_categories,
            "evidence_available": len(self.detection_history),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset(self):
        """Reset agent for new session"""
        self.total_risk = 0.0
        self.turn_count = 0
        self.detection_history = []
        print(f"🔄 Session {self.session_id} reset")

    # ============================================================
    # HOUR 12: IMPROVED SCAM LANGUAGE RULES
    # ============================================================

    def _enhanced_scam_detection(self, text: str) -> Dict[str, Any]:
        """
        Enhanced detection for obvious scam phrases
        Detects multiple scam indicators in same sentence
        """
        text_lower = text.lower()
        
        # Scam indicator categories for multi-factor detection
        scam_indicators = {
            "payment_request": ["bitcoin", "gift card", "send money", "wire transfer", "paypal", "venmo", "google pay", "phonepe"],
            "urgency": ["immediately", "right now", "urgent", "asap", "don't hang up", "jaldi", "turant", "abhi"],
            "threat": ["arrest", "warrant", "jail", "lawsuit", "court", "police", "pakda", "case"],
            "authority": ["irs", "fbi", "police", "government", "bank", "microsoft", "rbi", "income tax"],
            "identity": ["otp", "aadhaar", "pan", "ssn", "password", "pin", "bank account"]
        }
        
        # Count triggered categories
        triggered = [cat for cat, keywords in scam_indicators.items() if any(kw in text_lower for kw in keywords)]
        
        # Bonus risk for multiple indicators
        if len(triggered) >= 3:
            return {"bonus_risk": 0.15, "reason": f"Multiple scam indicators: {', '.join(triggered)}"}
        elif len(triggered) >= 2:
            return {"bonus_risk": 0.08, "reason": f"Multiple indicators: {', '.join(triggered)}"}
        
        return {"bonus_risk": 0.0, "reason": None}

    # ============================================================
    # HOUR 13: SHORT AND CLEAR EXPLANATIONS
    # ============================================================

    def _get_judge_explanation(self, categories: List[str], keywords: List[str], risk: float) -> str:
        """
        Generate judge-friendly, short, clear explanation
        Used for demo presentation
        """
        if not categories:
            return "✅ No scam indicators detected"
        
        # Short, clear explanations for judges
        short_explanations = {
            "payment_request": "💰 Asks for money/payment",
            "identity_theft": "🆔 Requests personal info (OTP/Aadhaar/Bank)",
            "threat": "⚠️ Uses threats or intimidation",
            "fake_authority": "👮 Pretends to be official/authority",
            "urgency": "⏰ Creates artificial urgency/pressure",
            "scam_phrases": "📝 Uses known scam phrases"
        }
        
        detected = [short_explanations[cat] for cat in categories if cat in short_explanations]
        
        if detected:
            # Limit to 2 reasons for brevity
            main_reasons = detected[:2]
            explanation = "; ".join(main_reasons)
            
            # Add top keyword if exists
            if keywords:
                top_keyword = keywords[0].replace("[", "").replace("]", "")
                explanation += f" (keyword: '{top_keyword}')"
            
            # Add urgency indicator for demo
            if risk >= 0.6:
                explanation = "🔴 " + explanation + " - INTERVENE NOW"
            elif risk >= 0.4:
                explanation = "🟠 " + explanation + " - ESCALATE"
            elif risk >= 0.2:
                explanation = "🟡 " + explanation
            
            return explanation
        
        return "⚠️ Suspicious patterns detected"

    # ============================================================
    # HOUR 15: PARTIAL TRANSCRIPT HANDLING
    # ============================================================

    def analyze_partial(self, text: str, is_final: bool = False, min_length: int = 5) -> DetectionResult:
        """
        Handle partial/incomplete transcripts with stability
        
        Args:
            text: Partial transcript text
            is_final: Whether this is the final version of this utterance
            min_length: Minimum characters for meaningful analysis
        """
        # Handle empty or very short text
        if not text or len(text.strip()) < min_length:
            return DetectionResult(
                turn_id=f"{self.session_id}_partial",
                session_id=self.session_id,
                timestamp=datetime.now().isoformat(),
                transcript=text,
                detected_keywords=[],
                detected_categories=[],
                risk_score=0.0,
                risk_level="PENDING",
                scam_type="insufficient_data",
                explanation="⏳ Waiting for more speech...",
                reason_codes=[],
                evidence_hash=""
            )
        
        # Run full analysis
        result = self.analyze_transcript(text)
        
        # Adjust confidence for partial transcripts
        if not is_final:
            # Reduce confidence by 20% for non-final chunks
            result.risk_score = round(result.risk_score * 0.8, 3)
            result.explanation += " (partial - awaiting more context)"
        
        return result

    def process_stream_turns(self, turns: List[Dict]) -> List[DetectionResult]:
        """
        Process a stream of transcript turns with accumulation
        
        Args:
            turns: List of dicts with 'text', 'speaker', 'is_final'
        """
        results = []
        accumulated_text = ""
        
        for turn in turns:
            text = turn.get('text', '')
            is_final = turn.get('is_final', False)
            speaker = turn.get('speaker', 'caller')
            
            # Accumulate text for context
            accumulated_text += " " + text
            
            if is_final:
                # Process complete utterance
                result = self.analyze_transcript(accumulated_text.strip(), speaker)
                accumulated_text = ""
            else:
                # Process partial with lower confidence
                result = self.analyze_partial(text, is_final)
            
            results.append(result)
            
            # Early alert for high risk
            if result.risk_score >= config.RISK_THRESHOLDS.get("high", 0.5):
                result.explanation += " [⚠️ EARLY ALERT - INTERVENE NOW]"
        
        return results


# Quick test
if __name__ == "__main__":
    agent = LinguisticAgent()
    
    test_texts = [
        ("English scam", "Send me $500 in bitcoin immediately"),
        ("Hinglish scam", "Mujhe 500 rupees bhejo, nahi toh police pakad legi"),
        ("Hindi scam", "जल्दी करो, नहीं तो गिरफ्तारी हो जाएगी"),
        ("Mixed scam", "Aapka account compromised hai, OTP batao warna account freeze"),
        ("Normal call", "Namaste, main apne account ke baare mein pooch raha tha")
    ]
    
    for name, text in test_texts:
        result = agent.analyze_transcript(text)
        print(f"\n📞 {name}: '{text[:50]}...'")
        print(f"   Risk: {result.risk_score:.0%} ({result.risk_level})")
        print(f"   Type: {result.scam_type}")
        print(f"   Keywords: {result.detected_keywords[:4]}")
    
    print("\n" + "="*50)
    print("SESSION SUMMARY:")
    print(json.dumps(agent.get_session_summary(), indent=2))