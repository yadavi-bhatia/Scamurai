"""
PERSON 2 - MONEY RISK ANALYZER (Hour 25)
Detects large money amounts and analyzes payment pressure
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MoneyRiskResult:
    """Result of money risk analysis"""
    amount_detected: bool
    amount_value: Optional[float]
    amount_currency: str  # "USD", "INR", "UNKNOWN"
    is_large_amount: bool
    pressure_level: str  # "low", "medium", "high"
    urgency_indicators: List[str]
    payment_methods: List[str]
    risk_score: float
    explanation: str


class MoneyRiskAnalyzer:
    """
    Analyzes money-related scam indicators
    - Detects money amounts (USD and INR)
    - Identifies large amounts that trigger escalation
    - Detects payment methods and urgency
    """
    
    # Currency patterns
    USD_PATTERN = re.compile(r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', re.IGNORECASE)
    INR_PATTERN = re.compile(r'[₹Rs\.]*\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupees|rs\.?|inr)?', re.IGNORECASE)
    
    # Large amount thresholds
    LARGE_THRESHOLDS = {
        "USD": 1000,      # $1000+
        "INR": 50000,     # ₹50,000+
        "UNKNOWN": 10000  # Default threshold
    }
    
    # Payment methods (scam indicators)
    PAYMENT_METHODS = {
        "crypto": ["bitcoin", "btc", "crypto", "ethereum", "usdt", "tether"],
        "gift_card": ["gift card", "giftcard", "google play", "itunes", "amazon card"],
        "wire_transfer": ["wire transfer", "bank transfer", "western union", "moneygram"],
        "upi": ["google pay", "phonepe", "paytm", "upi", "gpay", "phone pay"],
        "cash": ["cash", "cashapp", "venmo", "paypal"]
    }
    
    # Urgency indicators
    URGENCY_INDICATORS = [
        "immediately", "right now", "urgent", "asap", "act now",
        "don't wait", "hurry", "quickly", "today only",
        "jaldi", "abhi", "turant", "time kam hai", "last chance"
    ]
    
    # Pressure escalation phrases
    PRESSURE_PHRASES = [
        "or else", "otherwise", "if not", "warning", "final",
        "last chance", "will be", "you'll be", "consequences",
        "warna", "nahi toh", "final warning"
    ]
    
    def __init__(self):
        self.version = "1.0.0"
        print("[MONEY] Money risk analyzer ready")
    
    def analyze(self, text: str) -> MoneyRiskResult:
        """
        Analyze text for money-related scam indicators
        
        Args:
            text: Transcript text to analyze
        
        Returns:
            MoneyRiskResult with detailed analysis
        """
        text_lower = text.lower()
        
        # Detect amounts
        usd_amount = self._detect_usd(text)
        inr_amount = self._detect_inr(text)
        
        amount_detected = usd_amount is not None or inr_amount is not None
        amount_value = None
        amount_currency = "UNKNOWN"
        
        if usd_amount is not None:
            amount_value = usd_amount
            amount_currency = "USD"
        elif inr_amount is not None:
            amount_value = inr_amount
            amount_currency = "INR"
        
        # Check if large amount
        threshold = self.LARGE_THRESHOLDS.get(amount_currency, self.LARGE_THRESHOLDS["UNKNOWN"])
        is_large_amount = amount_detected and amount_value and amount_value >= threshold
        
        # Detect payment methods
        payment_methods = self._detect_payment_methods(text_lower)
        
        # Detect urgency and pressure
        urgency_indicators = self._detect_urgency(text_lower)
        pressure_level = self._detect_pressure_level(text_lower, urgency_indicators)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            amount_detected, is_large_amount, 
            payment_methods, pressure_level
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            amount_detected, amount_value, amount_currency,
            is_large_amount, payment_methods, pressure_level
        )
        
        return MoneyRiskResult(
            amount_detected=amount_detected,
            amount_value=amount_value,
            amount_currency=amount_currency,
            is_large_amount=is_large_amount,
            pressure_level=pressure_level,
            urgency_indicators=urgency_indicators[:3],
            payment_methods=payment_methods,
            risk_score=risk_score,
            explanation=explanation
        )
    
    def _detect_usd(self, text: str) -> Optional[float]:
        """Detect USD amount"""
        match = self.USD_PATTERN.search(text)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
            except:
                pass
        return None
    
    def _detect_inr(self, text: str) -> Optional[float]:
        """Detect INR amount"""
        match = self.INR_PATTERN.search(text)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
            except:
                pass
        return None
    
    def _detect_payment_methods(self, text: str) -> List[str]:
        """Detect mentioned payment methods"""
        detected = []
        for method, keywords in self.PAYMENT_METHODS.items():
            for keyword in keywords:
                if keyword in text:
                    detected.append(method)
                    break
        return list(set(detected))
    
    def _detect_urgency(self, text: str) -> List[str]:
        """Detect urgency indicators"""
        detected = []
        for indicator in self.URGENCY_INDICATORS:
            if indicator in text:
                detected.append(indicator)
        return detected
    
    def _detect_pressure_level(self, text: str, urgency_indicators: List) -> str:
        """Determine pressure level based on urgency and threats"""
        pressure_count = len(urgency_indicators)
        
        # Check for threat phrases
        has_threat = any(phrase in text for phrase in self.PRESSURE_PHRASES)
        
        if pressure_count >= 3 or has_threat:
            return "high"
        elif pressure_count >= 1:
            return "medium"
        return "low"
    
    def _calculate_risk_score(self, amount_detected: bool, is_large: bool,
                              payment_methods: List, pressure_level: str) -> float:
        """Calculate money-related risk score (0-1)"""
        risk = 0.0
        
        if amount_detected:
            risk += 0.15
            if is_large:
                risk += 0.20
        
        if payment_methods:
            risk += 0.10 * min(len(payment_methods), 2)
        
        if pressure_level == "high":
            risk += 0.25
        elif pressure_level == "medium":
            risk += 0.15
        
        return min(1.0, risk)
    
    def _generate_explanation(self, amount_detected: bool, amount_value: float,
                              amount_currency: str, is_large: bool,
                              payment_methods: List, pressure_level: str) -> str:
        """Generate human-readable explanation"""
        if not amount_detected and not payment_methods:
            return "No money-related scam indicators"
        
        parts = []
        
        if amount_detected:
            if is_large:
                parts.append(f"LARGE {amount_currency} {amount_value:,.0f} requested")
            else:
                parts.append(f"{amount_currency} {amount_value:,.0f} requested")
        
        if payment_methods:
            methods_str = ", ".join(payment_methods)
            parts.append(f"Payment via {methods_str}")
        
        if pressure_level == "high":
            parts.append("HIGH pressure tactics with threats")
        elif pressure_level == "medium":
            parts.append("Urgency pressure detected")
        
        result = " | ".join(parts)
        
        if is_large and pressure_level == "high":
            result = "⚠️ " + result + " - CRITICAL MONEY RISK"
        
        return result
    
    def get_alert_priority(self, result: MoneyRiskResult) -> str:
        """Get alert priority based on money risk"""
        if result.is_large_amount and result.pressure_level == "high":
            return "CRITICAL"
        elif result.is_large_amount or result.pressure_level == "high":
            return "HIGH"
        elif result.amount_detected or result.payment_methods:
            return "MEDIUM"
        return "LOW"


# Quick test
if __name__ == "__main__":
    analyzer = MoneyRiskAnalyzer()
    
    test_cases = [
        "Send me $5000 in bitcoin immediately",
        "Please pay ₹1,00,000 via Google Pay right now",
        "You need to send $500 or you will be arrested",
        "Just pay $50 for the service",
        "Hello, I'm calling about your account"
    ]
    
    print("\n" + "=" * 70)
    print("MONEY RISK ANALYZER TEST")
    print("=" * 70)
    
    for text in test_cases:
        result = analyzer.analyze(text)
        print(f"\nTEXT: '{text[:60]}...'")
        print(f"   AMOUNT: {result.amount_value} {result.amount_currency if result.amount_detected else 'None'}")
        print(f"   LARGE: {result.is_large_amount}")
        print(f"   PAYMENT METHODS: {result.payment_methods}")
        print(f"   PRESSURE: {result.pressure_level}")
        print(f"   RISK SCORE: {result.risk_score:.0%}")
        print(f"   EXPLANATION: {result.explanation}")