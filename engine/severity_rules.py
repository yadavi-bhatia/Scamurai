
"""Hour 31: Severity Rules - High-value scams trigger stronger prompts."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ActionRule:
    """Rule for determining actions based on severity."""
    severity: SeverityLevel
    should_block: bool
    should_report: bool
    should_alert_contacts: bool
    alert_priority: str
    user_message: str
    requires_confirmation: bool


class SeverityRulesEngine:
    """
    Severity-based action rules.
    High-value scams trigger stronger prompts and actions.
    """
    
    # High value threshold (₹)
    HIGH_VALUE_THRESHOLD = 50000
    CRITICAL_VALUE_THRESHOLD = 200000
    
    def __init__(self):
        self.rules = self._initialize_rules()
        self.action_history: List[Dict] = []
    
    def _initialize_rules(self) -> Dict[SeverityLevel, ActionRule]:
        """Initialize rules for each severity level."""
        return {
            SeverityLevel.CRITICAL: ActionRule(
                severity=SeverityLevel.CRITICAL,
                should_block=True,
                should_report=True,
                should_alert_contacts=True,
                alert_priority="emergency",
                user_message="🔴 CRITICAL: Immediate action required! This is a confirmed scam with high value at risk.",
                requires_confirmation=False
            ),
            SeverityLevel.HIGH: ActionRule(
                severity=SeverityLevel.HIGH,
                should_block=True,
                should_report=True,
                should_alert_contacts=True,
                alert_priority="high",
                user_message="⚠️ HIGH RISK: Scam detected. Block this number and share alert with trusted contacts.",
                requires_confirmation=False
            ),
            SeverityLevel.MEDIUM: ActionRule(
                severity=SeverityLevel.MEDIUM,
                should_block=False,
                should_report=True,
                should_alert_contacts=False,
                alert_priority="normal",
                user_message="⚠️ MEDIUM RISK: Suspicious call detected. Consider reporting this number.",
                requires_confirmation=True
            ),
            SeverityLevel.LOW: ActionRule(
                severity=SeverityLevel.LOW,
                should_block=False,
                should_report=False,
                should_alert_contacts=False,
                alert_priority="low",
                user_message="ℹ️ LOW RISK: Call appears safe. No action needed.",
                requires_confirmation=False
            )
        }
    
    def determine_severity(
        self,
        verdict: str,
        risk_score: float,
        detected_amount: Optional[float] = None,
        family_impersonation: bool = False,
        deepfake_flag: bool = False
    ) -> SeverityLevel:
        """
        Determine severity level based on multiple factors.
        High-value scams trigger stronger prompts.
        """
        # Critical: Very high risk or huge amount
        if risk_score >= 90:
            return SeverityLevel.CRITICAL
        if detected_amount and detected_amount >= self.CRITICAL_VALUE_THRESHOLD:
            return SeverityLevel.CRITICAL
        
        # High: High risk or large amount or family impersonation
        if risk_score >= 70:
            return SeverityLevel.HIGH
        if detected_amount and detected_amount >= self.HIGH_VALUE_THRESHOLD:
            return SeverityLevel.HIGH
        if family_impersonation or deepfake_flag:
            return SeverityLevel.HIGH
        
        # Medium: Suspicious
        if risk_score >= 40:
            return SeverityLevel.MEDIUM
        
        # Low: Safe
        return SeverityLevel.LOW
    
    def get_actions_for_severity(self, severity: SeverityLevel) -> ActionRule:
        """Get actions required for a severity level."""
        return self.rules.get(severity, self.rules[SeverityLevel.LOW])
    
    def evaluate_and_get_actions(
        self,
        verdict: str,
        risk_score: float,
        detected_amount: Optional[float] = None,
        family_impersonation: bool = False,
        deepfake_flag: bool = False
    ) -> Tuple[SeverityLevel, ActionRule, Dict[str, Any]]:
        """
        Evaluate severity and return recommended actions.
        """
        severity = self.determine_severity(
            verdict=verdict,
            risk_score=risk_score,
            detected_amount=detected_amount,
            family_impersonation=family_impersonation,
            deepfake_flag=deepfake_flag
        )
        
        actions = self.get_actions_for_severity(severity)
        
        # Additional context for the user
        context = {
            "severity": severity.value,
            "risk_score": risk_score,
            "detected_amount": detected_amount,
            "recommended_block": actions.should_block,
            "recommended_report": actions.should_report,
            "recommended_alert": actions.should_alert_contacts,
            "user_message": actions.user_message,
            "requires_confirmation": actions.requires_confirmation
        }
        
        # Add amount-specific messaging
        if detected_amount and detected_amount >= self.HIGH_VALUE_THRESHOLD:
            context["amount_warning"] = f"💰 Large amount at risk: ₹{detected_amount:,.2f}"
            context["user_message"] = f"💰 {context['user_message']} Amount at risk: ₹{detected_amount:,.2f}"
        
        if family_impersonation:
            context["family_warning"] = "👨‍👩‍👧 Family impersonation detected! This is a common scam tactic."
            context["user_message"] = f"👨‍👩‍👧 {context['user_message']}"
        
        if deepfake_flag:
            context["deepfake_warning"] = "🤖 AI deepfake voice detected! The caller may be using voice cloning."
            context["user_message"] = f"🤖 {context['user_message']}"
        
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "severity": severity.value,
            "risk_score": risk_score,
            "detected_amount": detected_amount,
            "actions": {
                "block": actions.should_block,
                "report": actions.should_report,
                "alert": actions.should_alert_contacts
            }
        })
        
        return severity, actions, context
    
    def get_alert_prompt(self, severity: SeverityLevel, amount: Optional[float] = None) -> str:
        """Get user-friendly alert prompt based on severity."""
        prompts = {
            SeverityLevel.CRITICAL: "🔴 CRITICAL ALERT! This is a confirmed scam. Block immediately and share with trusted contacts!",
            SeverityLevel.HIGH: "⚠️ HIGH RISK SCAM DETECTED! Block this number and alert your trusted contacts.",
            SeverityLevel.MEDIUM: "⚠️ Suspicious call detected. Consider reporting this number.",
            SeverityLevel.LOW: "ℹ️ Call appears safe. No action needed."
        }
        
        prompt = prompts.get(severity, prompts[SeverityLevel.LOW])
        
        if amount and amount >= self.HIGH_VALUE_THRESHOLD:
            prompt = f"💰 {prompt} Amount at risk: ₹{amount:,.2f}"
        
        return prompt
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get severity rule statistics."""
        severity_counts = {s.value: 0 for s in SeverityLevel}
        for entry in self.action_history:
            severity = entry.get("severity", "low")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            "total_evaluations": len(self.action_history),
            "severity_distribution": severity_counts,
            "high_value_threshold": self.HIGH_VALUE_THRESHOLD,
            "critical_value_threshold": self.CRITICAL_VALUE_THRESHOLD
        }


# Global instance
severity_engine = SeverityRulesEngine()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 31: Severity Rules")
    print("="*50)
    
    # Test cases
    test_cases = [
        ("DANGEROUS", 95, 100000, False, False),
        ("DANGEROUS", 85, 30000, True, False),
        ("DANGEROUS", 75, None, False, True),
        ("SUSPICIOUS", 55, None, False, False),
        ("SAFE", 10, None, False, False),
    ]
    
    for verdict, score, amount, family, deepfake in test_cases:
        severity, actions, context = severity_engine.evaluate_and_get_actions(
            verdict=verdict,
            risk_score=score,
            detected_amount=amount,
            family_impersonation=family,
            deepfake_flag=deepfake
        )
        print(f"\n📞 {verdict} (Score: {score})")
        print(f"   Severity: {severity.value}")
        print(f"   Actions: Block={actions.should_block}, Report={actions.should_report}, Alert={actions.should_alert_contacts}")
        print(f"   Message: {context['user_message'][:60]}...")
    
    print("\n✅ Hour 31 Complete: Severity rules ready!")
