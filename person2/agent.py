"""
PERSON 2 - LINGUISTIC AGENT (English Only)
Complete scam detection - English language only
"""

import json
import re
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

VERSION = "2.1.0"
STATUS = "PRODUCTION READY"

CONFIG = {
    "risk_thresholds": {
        "critical": 0.70,
        "high": 0.50,
        "medium": 0.30,
        "low": 0.10
    },
    "large_amount_threshold": 10000
}

# ============================================================
# SCAM KEYWORD DATABASE (English Only)
# ============================================================
SCAM_KEYWORDS = {
    "critical_payment": {
        "keywords": [
            "bitcoin", "gift card", "western union", "moneygram", "crypto",
            "send money", "wire transfer", "paypal", "venmo", "cash app"
        ],
        "weight": 0.45,
        "output": "Payment requested"
    },
    "critical_identity": {
        "keywords": [
            "otp", "social security", "bank account", "password",
            "credit card", "debit card", "ssn", "aadhaar", "pan card"
        ],
        "weight": 0.40,
        "output": "Personal information requested"
    },
    "high_threat": {
        "keywords": [
            "arrest", "warrant", "jail", "police", "lawsuit", "court",
            "freeze", "suspend", "legal action", "fbi", "irs"
        ],
        "weight": 0.35,
        "output": "Threats or intimidation used"
    },
    "high_urgency": {
        "keywords": [
            "immediately", "right now", "urgent", "don't hang up",
            "asap", "act now", "final warning", "last chance"
        ],
        "weight": 0.25,
        "output": "Urgency pressure tactics"
    },
    "medium_authority": {
        "keywords": [
            "irs", "bank", "police", "microsoft", "amazon", "paypal",
            "government", "social security administration"
        ],
        "weight": 0.18,
        "output": "Fake authority impersonation"
    },
    "medium_scam_phrases": {
        "keywords": [
            "account compromised", "suspicious activity", "verify identity",
            "security alert", "fraud alert", "kyc pending"
        ],
        "weight": 0.12,
        "output": "Known scam phrases detected"
    }
}

# Family impersonation keywords (English only)
FAMILY_IMPERSONATION_KEYWORDS = [
    "i'm your son", "i'm your daughter", "it's me your child",
    "your son is in trouble", "your daughter needs help",
    "mom", "dad", "mother", "father", "grandma", "grandpa", "child"
]

# Money pattern
MONEY_PATTERN = re.compile(r'\$\d+(?:,\d+)*(?:\.\d+)?', re.IGNORECASE)


# ============================================================
# DATA CLASSES
# ============================================================
@dataclass
class DetectionResult:
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
    money_amount_mentioned: bool = False
    family_impersonation: bool = False
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FinalHandoff:
    session_id: str
    timestamp: str
    total_turns: int
    max_risk_score: float
    final_risk_level: str
    scam_type: str
    detected_keywords: List[str]
    detected_categories: List[str]
    money_amount_mentioned: bool
    family_impersonation: bool
    summary: str
    recommended_action: str
    alert_message: str
    version: str = VERSION
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


# ============================================================
# MAIN LINGUISTIC AGENT
# ============================================================
class LinguisticAgent:
    def __init__(self, session_id: Optional[str] = None):
        from uuid import uuid4
        self.session_id = session_id or str(uuid4())[:8]
        self.turn_count = 0
        self.history: List[DetectionResult] = []
        self.processing_times: List[float] = []
        self.alert_triggered = False
        
        self.patterns = self._compile_patterns()
        self.family_pattern = re.compile(r'\b(?:' + '|'.join(FAMILY_IMPERSONATION_KEYWORDS) + r')\b', re.IGNORECASE)
        
        print(f"[READY] Linguistic Agent v{VERSION}")
        print(f"   Session: {self.session_id}")
        print(f"   Language: English Only")
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        patterns = {}
        for category, cat_data in SCAM_KEYWORDS.items():
            escaped = [re.escape(kw) for kw in cat_data["keywords"]]
            patterns[category] = re.compile(r'\b(?:' + '|'.join(escaped) + r')\b', re.IGNORECASE)
        return patterns
    
    def _detect_money_amount(self, text: str) -> Tuple[bool, int]:
        if MONEY_PATTERN.search(text):
            numbers = re.findall(r'\b\d+\b', text)
            for num in numbers:
                try:
                    amount = int(num)
                    if amount >= CONFIG["large_amount_threshold"]:
                        return True, amount
                except:
                    pass
            return True, 0
        return False, 0
    
    def _detect_family_impersonation(self, text: str) -> bool:
        return bool(self.family_pattern.search(text))
    
    def analyze(self, text: str) -> DetectionResult:
        start_time = time.time()
        self.turn_count += 1
        turn_id = f"{self.session_id}_{self.turn_count:04d}"
        
        if not text or len(text.strip()) < 3:
            return self._empty_result(turn_id, text)
        
        detected_cats = []
        detected_kws = []
        total_risk = 0.0
        
        for category, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_cats.append(category)
                detected_kws.extend(matches[:3])
                total_risk += SCAM_KEYWORDS[category]["weight"] * min(len(matches), 2) / 2
        
        money_detected, money_amount = self._detect_money_amount(text)
        if money_detected:
            total_risk += 0.10
            detected_kws.append(f"[MONEY:{money_amount}]" if money_amount else "[MONEY]")
        
        family_impersonation = self._detect_family_impersonation(text)
        if family_impersonation:
            total_risk += 0.15
            detected_kws.append("[FAMILY_IMPERSONATION]")
            if "medium_authority" not in detected_cats:
                detected_cats.append("medium_authority")
        
        total_risk = min(1.0, total_risk)
        
        risk_level, action, verdict = self._get_risk_level(total_risk)
        scam_type = self._get_scam_type(detected_cats)
        explanation = self._get_explanation(detected_cats, detected_kws, total_risk, money_detected, family_impersonation)
        reason_codes = self._get_reason_codes(detected_cats)
        
        evidence_str = f"{turn_id}|{self.session_id}|{text}|{total_risk}|{datetime.now().isoformat()}"
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()[:16]
        
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
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
            evidence_hash=evidence_hash,
            money_amount_mentioned=money_detected,
            family_impersonation=family_impersonation,
            processing_time_ms=round(processing_time, 1)
        )
        
        self.history.append(result)
        
        if total_risk >= CONFIG["risk_thresholds"]["high"] and not self.alert_triggered:
            self.alert_triggered = True
        
        return result
    
    def _get_risk_level(self, risk: float) -> Tuple[str, str, str]:
        if risk >= CONFIG["risk_thresholds"]["critical"]:
            return ("CRITICAL", "INTERVENE NOW", "SCAM CONFIRMED")
        elif risk >= CONFIG["risk_thresholds"]["high"]:
            return ("HIGH", "ESCALATE NOW", "SCAM LIKELY")
        elif risk >= CONFIG["risk_thresholds"]["medium"]:
            return ("MEDIUM", "MONITOR", "SUSPICIOUS")
        elif risk >= CONFIG["risk_thresholds"]["low"]:
            return ("LOW", "REVIEW", "CAUTION")
        return ("NONE", "NONE", "SAFE")
    
    def _get_scam_type(self, categories: List[str]) -> str:
        priority = ["critical_payment", "critical_identity", "high_threat", "medium_authority"]
        type_map = {
            "critical_payment": "payment_scam",
            "critical_identity": "identity_theft_scam",
            "high_threat": "government_impersonation",
            "high_urgency": "pressure_tactic",
            "medium_authority": "authority_impersonation"
        }
        for cat in priority:
            if cat in categories:
                return type_map.get(cat, "unknown")
        return "none"
    
    def _get_explanation(self, categories: List[str], keywords: List[str], risk: float, 
                         money_detected: bool, family_impersonation: bool) -> str:
        if not categories and not money_detected and not family_impersonation:
            return "SAFE: No scam indicators detected"
        
        detected_outputs = []
        for cat in categories[:2]:
            if cat in SCAM_KEYWORDS:
                detected_outputs.append(SCAM_KEYWORDS[cat]["output"])
        
        if money_detected:
            detected_outputs.append("Large money amount mentioned")
        
        if family_impersonation:
            detected_outputs.append("Family member impersonation detected")
        
        result = "; ".join(detected_outputs)
        
        if keywords:
            clean_kws = [kw.replace("[MONEY]", "money").replace("[FAMILY_IMPERSONATION]", "family impersonation") 
                        for kw in keywords[:2]]
            if clean_kws:
                result += f" (keyword: {clean_kws[0]})"
        
        if risk >= 0.6:
            result = "[CRITICAL] " + result + " - INTERVENE NOW"
        elif risk >= 0.4:
            result = "[HIGH] " + result + " - ESCALATE"
        elif risk >= 0.2:
            result = "[MEDIUM] " + result
        
        return result
    
    def _get_reason_codes(self, categories: List[str]) -> List[str]:
        code_map = {
            "critical_payment": "R01", "critical_identity": "R02",
            "high_threat": "R03", "high_urgency": "R04",
            "medium_authority": "R05", "medium_scam_phrases": "R06"
        }
        return [code_map[cat] for cat in categories if cat in code_map]
    
    def _empty_result(self, turn_id: str, text: str) -> DetectionResult:
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
            evidence_hash="",
            money_amount_mentioned=False,
            family_impersonation=False
        )
    
    def get_handoff(self) -> FinalHandoff:
        if not self.history:
            return FinalHandoff(
                session_id=self.session_id,
                timestamp=datetime.now().isoformat(),
                total_turns=0,
                max_risk_score=0.0,
                final_risk_level="SAFE",
                scam_type="none",
                detected_keywords=[],
                detected_categories=[],
                money_amount_mentioned=False,
                family_impersonation=False,
                summary="No data analyzed",
                recommended_action="NONE",
                alert_message="No scam detected"
            )
        
        max_result = max(self.history, key=lambda x: x.risk_score)
        max_risk = max_result.risk_score
        
        all_keywords = set()
        all_categories = set()
        money_mentioned = False
        family_impersonation = False
        
        for r in self.history:
            all_keywords.update(r.detected_keywords)
            all_categories.update(r.detected_categories)
            if r.money_amount_mentioned:
                money_mentioned = True
            if r.family_impersonation:
                family_impersonation = True
        
        if max_risk >= CONFIG["risk_thresholds"]["critical"]:
            final_risk = "DANGEROUS"
            action = "BLOCK_CALL"
            alert_msg = "CRITICAL: Scam confirmed. Block the number."
        elif max_risk >= CONFIG["risk_thresholds"]["high"]:
            final_risk = "SUSPICIOUS"
            action = "ESCALATE"
            alert_msg = "HIGH RISK: Scam likely. Escalate to human operator."
        elif max_risk >= CONFIG["risk_thresholds"]["medium"]:
            final_risk = "LOW_RISK"
            action = "MONITOR"
            alert_msg = "MEDIUM RISK: Suspicious activity detected."
        else:
            final_risk = "SAFE"
            action = "NONE"
            alert_msg = "No scam detected"
        
        return FinalHandoff(
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            total_turns=len(self.history),
            max_risk_score=round(max_risk, 3),
            final_risk_level=final_risk,
            scam_type=max_result.scam_type,
            detected_keywords=list(all_keywords)[:10],
            detected_categories=list(all_categories),
            money_amount_mentioned=money_mentioned,
            family_impersonation=family_impersonation,
            summary=f"{final_risk}: {max_result.explanation[:100]}",
            recommended_action=action,
            alert_message=alert_msg
        )
    
    def reset(self):
        self.turn_count = 0
        self.history = []
        self.processing_times = []
        self.alert_triggered = False
        print(f"[RESET] Session {self.session_id} reset")


if __name__ == "__main__":
    agent = LinguisticAgent("test")
    
    test_phrases = [
        "Send me $50000 in bitcoin immediately",
        "Mom, it's me your son. I need money for bail.",
        "This is the IRS. You will be arrested.",
        "Hello, I'm calling to confirm my appointment"
    ]
    
    print("\n" + "=" * 70)
    print("PERSON 2 - ENGLISH ONLY TEST")
    print("=" * 70)
    
    for text in test_phrases:
        result = agent.analyze(text)
        print(f"\nINPUT: '{text}'")
        print(f"   RISK: {result.risk_score:.0%} ({result.risk_level})")
        print(f"   TYPE: {result.scam_type}")
        print(f"   MONEY: {result.money_amount_mentioned}")
        print(f"   FAMILY: {result.family_impersonation}")
        print(f"   OUTPUT: {result.explanation}")