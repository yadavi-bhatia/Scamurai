"""
PERSON 2 - IMPERSONATION DETECTOR (Hour 26)
Detects family impersonation and authority impersonation in text
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class ImpersonationResult:
    """Result of impersonation detection"""
    is_impersonation: bool
    impersonation_type: str  # "family", "authority", "both", "none"
    confidence: float
    detected_phrases: List[str]
    explanation: str


class ImpersonationDetector:
    """
    Detects impersonation attempts in scam calls
    - Family impersonation: "I'm your son/daughter", "Mom it's me"
    - Authority impersonation: "IRS calling", "Bank security team"
    """
    
    # Family impersonation patterns
    FAMILY_PATTERNS = {
        "direct_claim": [
            r"(?:i'?m|this is) your (?:son|daughter|child)",
            r"(?:i'?m|this is) (?:mom|dad|mother|father|grandma|grandpa)",
            r"it'?s me,? your (?:son|daughter)",
            r"your (?:son|daughter) is in trouble",
            r"(?:mom|dad|amma|appa|papa|mummy|daddy) (?:it'?s me|i need help)",
            r"beta (?:main hu|main hoon)",
            r"beti (?:main hu|main hoon)"
        ],
        "urgent_claim": [
            r"(?:i|we) need your help (?:urgently|immediately|right now)",
            r"please (?:help|save) (?:me|us)",
            r"(?:accident|emergency|trouble|jail|hospital)",
            r"i (?:don't|do not) have much time",
            r"please (?:don't|do not) tell anyone"
        ]
    }
    
    # Authority impersonation patterns
    AUTHORITY_PATTERNS = {
        "government": [
            r"(?:irs|income tax|government|rbi|sebi|ed|cbi|fbi|cia)",
            r"(?:tax department|revenue department|social security)",
            r"(?:central bureau|investigation agency)"
        ],
        "banking": [
            r"(?:bank of [a-z]+|sbi|hdfc|icici|axis|kotak|yes bank)",
            r"(?:fraud department|security team|risk department)",
            r"(?:kyc (?:team|department)|compliance team)"
        ],
        "tech_support": [
            r"(?:microsoft|apple|google|amazon|paypal) (?:support|security|team)",
            r"(?:tech (?:support|security)|computer (?:support|security))",
            r"(?:virus|malware|hacking) (?:detected|found)"
        ],
        "legal": [
            r"(?:lawyer|attorney|court|judge|legal department)",
            r"(?:lawsuit|case|summons|warrant) (?:filed|issued)",
            r"(?:legal action|police case|criminal case)"
        ]
    }
    
    # Urgency + Authority combo (high risk)
    URGENCY_WORDS = [
        "immediately", "urgent", "right now", "asap", "don't hang up",
        "jaldi", "abhi", "turant", "time nahi hai", "final warning"
    ]
    
    def __init__(self):
        self.version = "1.0.0"
        self._compile_patterns()
        print("[IMPERSONATION] Impersonation detector ready")
    
    def _compile_patterns(self):
        """Compile all regex patterns"""
        self.family_compiled = []
        for pattern_list in self.FAMILY_PATTERNS.values():
            for pattern in pattern_list:
                self.family_compiled.append(re.compile(pattern, re.IGNORECASE))
        
        self.authority_compiled = {}
        for category, patterns in self.AUTHORITY_PATTERNS.items():
            self.authority_compiled[category] = []
            for pattern in patterns:
                self.authority_compiled[category].append(re.compile(pattern, re.IGNORECASE))
    
    def detect(self, text: str) -> ImpersonationResult:
        """
        Detect impersonation in the given text
        
        Args:
            text: Transcript of the call
        
        Returns:
            ImpersonationResult with detection details
        """
        text_lower = text.lower()
        detected_phrases = []
        impersonation_types = []
        
        # Check family impersonation
        family_detected = self._detect_family_impersonation(text_lower, detected_phrases)
        if family_detected:
            impersonation_types.append("family")
        
        # Check authority impersonation
        authority_type = self._detect_authority_impersonation(text_lower, detected_phrases)
        if authority_type:
            impersonation_types.append(authority_type)
        
        # Determine final result
        if len(impersonation_types) >= 2:
            impersonation_type = "both"
            confidence = 0.85
        elif impersonation_types:
            impersonation_type = impersonation_types[0]
            confidence = 0.75
        else:
            impersonation_type = "none"
            confidence = 0.0
        
        # Generate explanation
        explanation = self._generate_explanation(impersonation_type, detected_phrases, text_lower)
        
        return ImpersonationResult(
            is_impersonation=impersonation_type != "none",
            impersonation_type=impersonation_type,
            confidence=confidence,
            detected_phrases=detected_phrases[:5],
            explanation=explanation
        )
    
    def _detect_family_impersonation(self, text: str, detected_phrases: List) -> bool:
        """Detect family impersonation patterns"""
        for pattern in self.family_compiled:
            match = pattern.search(text)
            if match:
                detected_phrases.append(f"family_claim: {match.group()}")
                return True
        return False
    
    def _detect_authority_impersonation(self, text: str, detected_phrases: List) -> str:
        """Detect authority impersonation and return the type"""
        for category, patterns in self.authority_compiled.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    detected_phrases.append(f"authority_{category}: {match.group()}")
                    return category
        return ""
    
    def _generate_explanation(self, imp_type: str, phrases: List, text: str) -> str:
        """Generate human-readable explanation"""
        if imp_type == "none":
            return "No impersonation detected"
        
        # Check for urgency combo
        urgency_detected = any(word in text for word in self.URGENCY_WORDS)
        
        if imp_type == "family":
            if urgency_detected:
                return "Family impersonation with URGENCY - someone pretending to be a family member in distress"
            return "Family impersonation detected - caller claims to be a family member"
        
        elif imp_type == "government":
            if urgency_detected:
                return "Government authority impersonation with URGENCY - creating fear of legal action"
            return "Government authority impersonation detected - fake official claiming legal authority"
        
        elif imp_type == "banking":
            if urgency_detected:
                return "Bank impersonation with URGENCY - pressuring for immediate action"
            return "Bank authority impersonation detected - fake bank official requesting information"
        
        elif imp_type == "tech_support":
            return "Tech support impersonation detected - fake technical support scam"
        
        elif imp_type == "legal":
            return "Legal authority impersonation detected - fake lawyer/court official"
        
        elif imp_type == "both":
            return "MULTIPLE IMPERSONATIONS - caller using both family and authority claims"
        
        return f"Impersonation detected: {imp_type}"
    
    def get_risk_contribution(self, result: ImpersonationResult) -> float:
        """Get risk score contribution from impersonation"""
        if not result.is_impersonation:
            return 0.0
        
        base_risk = 0.25
        if result.impersonation_type == "both":
            base_risk = 0.35
        elif result.impersonation_type == "family":
            base_risk = 0.30
        
        # Add urgency bonus
        if "URGENCY" in result.explanation:
            base_risk += 0.10
        
        return min(0.5, base_risk)
    
    def get_alert_message(self, result: ImpersonationResult) -> str:
        """Get alert message for impersonation"""
        if not result.is_impersonation:
            return ""
        
        messages = {
            "family": "⚠️ FAMILY IMPERSONATION: Someone is pretending to be your family member. Verify their identity before taking any action.",
            "government": "⚠️ GOVERNMENT IMPERSONATION: Fake official claiming legal authority. Government agencies never demand payment over phone.",
            "banking": "⚠️ BANK IMPERSONATION: Fake bank official. Banks never ask for OTP or passwords.",
            "tech_support": "⚠️ TECH SUPPORT IMPERSONATION: Fake tech support. Legitimate companies don't call about viruses.",
            "legal": "⚠️ LEGAL IMPERSONATION: Fake legal authority. Verify through official channels.",
            "both": "⚠️ MULTIPLE IMPERSONATIONS: Caller using multiple fake identities. This is a high-risk scam!"
        }
        
        return messages.get(result.impersonation_type, "⚠️ Impersonation detected. Verify caller identity.")


# Quick test
if __name__ == "__main__":
    detector = ImpersonationDetector()
    
    test_cases = [
        "Hello, this is the IRS calling. You have a warrant.",
        "Mom, it's me your son. I'm in jail. Please send money.",
        "This is Rajesh from SBI bank. Your KYC is pending.",
        "I'm calling from Microsoft support. Your computer has a virus.",
        "Hello, I'm calling about your appointment tomorrow."
    ]
    
    print("\n" + "=" * 70)
    print("IMPERSONATION DETECTOR TEST")
    print("=" * 70)
    
    for text in test_cases:
        result = detector.detect(text)
        print(f"\nTEXT: '{text[:60]}...'")
        print(f"   IMPERSONATION: {result.impersonation_type}")
        print(f"   CONFIDENCE: {result.confidence:.0%}")
        print(f"   EXPLANATION: {result.explanation}")
        print(f"   RISK CONTRIBUTION: {detector.get_risk_contribution(result):.0%}")