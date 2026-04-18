"""Consensus engine combining signals (robust, enum-safe)."""

from engine.models import RiskLevel


class ConsensusEngine:
    def __init__(self):
        # using 0–1 scale since your signals are normalized
        self.RISK_THRESHOLD_SUSPICIOUS = 0.4
        self.RISK_THRESHOLD_DANGEROUS = 0.7

    def _pick_risk(self, score):
        """
        Pick a RiskLevel member WITHOUT iterating or assuming names.
        We try common names; if not present, we fallback safely.
        """
        # try common names first (if your enum has them)
        name_map = [
            ("HIGH", "DANGEROUS"),
            ("MEDIUM", "SUSPICIOUS"),
            ("LOW", "SAFE"),
        ]

        # determine desired tier
        if score >= self.RISK_THRESHOLD_DANGEROUS:
            desired = 0  # HIGH/DANGEROUS
        elif score >= self.RISK_THRESHOLD_SUSPICIOUS:
            desired = 1  # MEDIUM/SUSPICIOUS
        else:
            desired = 2  # LOW/SAFE

        # try to fetch by common names
        for name in name_map[desired]:
            if hasattr(RiskLevel, name):
                return getattr(RiskLevel, name)

        # fallback: grab ANY member via __members__ (works for Enum/StrEnum)
        members = getattr(RiskLevel, "__members__", None)
        if members:
            # pick first/middle/last based on desired tier
            values = list(members.values())
            if desired == 0:
                return values[-1]
            elif desired == 1:
                return values[len(values)//2]
            else:
                return values[0]

        # last-resort: just return the class itself (stringify later)
        return RiskLevel

    def decide(self, signals):
        # signals expected in 0–1
        ling = signals.get("linguistic_score", 0.5)
        voice = signals.get("voice_risk", 0.5)
        money = signals.get("money_risk", 0.5)
        imp = signals.get("impersonation_score", 0.5)

        # weighted fusion
        final_score = (
            0.4 * ling +
            0.2 * voice +
            0.2 * money +
            0.2 * imp
        )

        reason_codes = []
        if ling > 0.7:
            reason_codes.append("high_linguistic_risk")
        if money > 0.7:
            reason_codes.append("money_pattern")
        if imp > 0.7:
            reason_codes.append("impersonation_pattern")

        final_risk = self._pick_risk(final_score)

        # safe stringify
        risk_value = getattr(final_risk, "value", str(final_risk))

        return {
            "risk_score": round(final_score, 2),
            "risk_level": str(risk_value),
            "reason_codes": reason_codes
        }


# =========================
# ENTRY POINT (used by your pipeline)
# =========================

def get_final_decision(signals):
    engine = ConsensusEngine()
    return engine.decide(signals)