class SignalInput:
    def _init_(self, **kwargs):
        self._dict_.update(kwargs)


class DecisionOutput:
    def _init_(self, risk_score=0.5, risk_level="LOW"):
        self.risk_score = risk_score
        self.risk_level = risk_level


class RiskWeights:
    def _init_(self):
        self.linguistic = 0.25
        self.impersonation = 0.25
        self.money = 0.25
        self.voice = 0.25


# -------- Enums --------

class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CallerType:
    UNKNOWN = "UNKNOWN"
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"


class ScamType:
    UNKNOWN = "UNKNOWN"
    OTP = "OTP"
    IMPERSONATION = "IMPERSONATION"
    FINANCIAL = "FINANCIAL"


class ConfidenceLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# -------- Person 4 extra models --------

class VoiceAnalysisResult:
    def _init_(self, **kwargs):
        self._dict_.update(kwargs)


class TranscriptAnalysisResult:
    def _init_(self, **kwargs):
        self._dict_.update(kwargs)


class ExotelMetadata:
    def _init_(self, **kwargs):
        self._dict_.update(kwargs)


class IncidentState:
    def _init_(self, **kwargs):
        self._dict_.update(kwargs)