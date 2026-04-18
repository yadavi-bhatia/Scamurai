"""
MONEY RISK ANALYZER - FINAL (PRODUCTION)
"""

import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class MoneyRiskResult:
    amount_detected: bool
    amount_value: Optional[float]
    amount_currency: str
    is_large_amount: bool
    pressure_level: str
    urgency_indicators: List[str]
    payment_methods: List[str]
    risk_score: float
    explanation: str


class MoneyRiskAnalyzer:

    USD_PATTERN = re.compile(r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)', re.IGNORECASE)
    INR_PATTERN = re.compile(r'(₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d+)', re.IGNORECASE)

    LARGE_THRESHOLDS = {
        "USD": 1000,
        "INR": 50000,
        "UNKNOWN": 10000
    }

    PAYMENT_METHODS = {
        "crypto": ["bitcoin", "btc", "crypto", "ethereum", "usdt"],
        "gift_card": ["gift card", "google play", "itunes", "amazon card"],
        "wire_transfer": ["wire transfer", "western union", "moneygram"],
        "upi": ["google pay", "phonepe", "paytm", "upi", "gpay"],
        "cash": ["cash", "paypal", "venmo"]
    }

    URGENCY_INDICATORS = [
        "immediately", "right now", "urgent", "asap",
        "act now", "don't wait", "hurry", "quickly",
        "jaldi", "abhi", "turant"
    ]

    PRESSURE_PHRASES = [
        "or else", "otherwise", "if not",
        "final warning", "last chance",
        "you'll be", "consequences",
        "warna", "nahi toh"
    ]

    def analyze(self, text):
        text = text.lower()
        result = self._internal_money_analysis(text)

        if isinstance(result, MoneyRiskResult):
            return result.risk_score
        return 0.0

    def _internal_money_analysis(self, text: str) -> MoneyRiskResult:

        usd = self._detect_usd(text)
        inr = self._detect_inr(text)

        amount_detected = False
        amount_value = None
        currency = "UNKNOWN"

        if usd:
            amount_detected = True
            amount_value = usd
            currency = "USD"
        elif inr:
            amount_detected = True
            amount_value = inr
            currency = "INR"

        is_large = False
        if amount_detected:
            threshold = self.LARGE_THRESHOLDS.get(currency, 10000)
            is_large = amount_value >= threshold

        payment_methods = self._detect_payment_methods(text)
        urgency = self._detect_urgency(text)
        pressure = self._detect_pressure_level(text, urgency)

        risk = self._calculate_risk_score(
            amount_detected, is_large, payment_methods, pressure, text
        )

        explanation = self._generate_explanation(
            amount_detected, amount_value, currency,
            is_large, payment_methods, pressure
        )

        return MoneyRiskResult(
            amount_detected,
            amount_value,
            currency,
            is_large,
            pressure,
            urgency,
            payment_methods,
            risk,
            explanation
        )

    def _detect_usd(self, text):
        match = self.USD_PATTERN.search(text)
        return float(match.group(1).replace(',', '')) if match else None

    def _detect_inr(self, text):
        match = self.INR_PATTERN.search(text)
        return float(match.group(2).replace(',', '')) if match else None

    def _detect_payment_methods(self, text):
        return [m for m, k in self.PAYMENT_METHODS.items() if any(x in text for x in k)]

    def _detect_urgency(self, text):
        return [u for u in self.URGENCY_INDICATORS if u in text]

    def _detect_pressure_level(self, text, urgency):
        if any(p in text for p in self.PRESSURE_PHRASES) or len(urgency) >= 2:
            return "high"
        elif len(urgency) == 1:
            return "medium"
        return "low"

    # 🔥 BOOSTED LOGIC
    def _calculate_risk_score(self, amount, large, methods, pressure, text):
        risk = 0.0

        if amount:
            risk += 0.25
            if large:
                risk += 0.25

        if methods:
            risk += 0.15 * min(len(methods), 2)

        if pressure == "high":
            risk += 0.30
        elif pressure == "medium":
            risk += 0.20

        # 🔥 INTELLIGENCE BOOSTS
        if "otp" in text:
            risk += 0.4

        if any(w in text for w in ["bank", "account", "transaction", "card"]):
            risk += 0.2

        if ("send" in text or "transfer" in text or "pay" in text) and pressure != "low":
            risk += 0.2

        if any(w in text for w in ["mom", "dad", "mother", "father"]):
            risk += 0.25

        return min(1.0, risk)

    def _generate_explanation(self, amount, value, currency, large, methods, pressure):
        if not amount:
            return "No money scam indicators"

        parts = [f"{'LARGE ' if large else ''}{currency} {value:,.0f}"]

        if methods:
            parts.append(f"via {', '.join(methods)}")

        if pressure == "high":
            parts.append("HIGH pressure")
        elif pressure == "medium":
            parts.append("Urgency")

        return " | ".join(parts)


# ✅ GLOBAL INSTANCE (CRITICAL)
money_risk_analyzer = MoneyRiskAnalyzer()