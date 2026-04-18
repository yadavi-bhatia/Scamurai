
"""Hour 22: Summary Validator - Validate demo summary flow."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
import json


class DemoSummary(BaseModel):
    """Demo summary structure for validation."""
    incident_id: str
    timestamp: str
    verdict: str
    verdict_icon: str
    risk_score: int
    caller_number: str
    victim_number: str
    primary_reason: str
    indicators: List[str]
    transcript_excerpt: str
    evidence_hash: str
    action_taken: str


class SummaryValidator:
    """Validate demo summary flow."""
    
    def __init__(self):
        self.validation_results = []
    
    def validate_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate summary data structure."""
        
        print("\n" + "="*70)
        print("📋 DEMO SUMMARY VALIDATION")
        print("="*70)
        
        results = {}
        
        # Check 1: Required fields exist
        print("\n🔍 Check 1: Required fields")
        required_fields = ["incident_id", "timestamp", "verdict", "risk_score"]
        missing = [f for f in required_fields if f not in summary_data]
        
        if missing:
            results["required_fields"] = {"valid": False, "missing": missing}
            print(f"   ❌ Missing: {missing}")
        else:
            results["required_fields"] = {"valid": True}
            print(f"   ✅ All required fields present")
        
        # Check 2: Data types
        print("\n🔍 Check 2: Data types")
        type_errors = []
        
        if "risk_score" in summary_data and not isinstance(summary_data["risk_score"], (int, float)):
            type_errors.append("risk_score must be number")
        if "indicators" in summary_data and not isinstance(summary_data["indicators"], list):
            type_errors.append("indicators must be list")
        
        if type_errors:
            results["data_types"] = {"valid": False, "errors": type_errors}
            print(f"   ❌ {type_errors}")
        else:
            results["data_types"] = {"valid": True}
            print(f"   ✅ Data types correct")
        
        # Check 3: Valid values
        print("\n🔍 Check 3: Valid values")
        value_errors = []
        
        if "risk_score" in summary_data:
            score = summary_data["risk_score"]
            if not (0 <= score <= 100):
                value_errors.append(f"risk_score {score} must be 0-100")
        
        valid_verdicts = ["SAFE", "SUSPICIOUS", "DANGEROUS"]
        if "verdict" in summary_data and summary_data["verdict"] not in valid_verdicts:
            value_errors.append(f"verdict must be one of {valid_verdicts}")
        
        if value_errors:
            results["valid_values"] = {"valid": False, "errors": value_errors}
            print(f"   ❌ {value_errors}")
        else:
            results["valid_values"] = {"valid": True}
            print(f"   ✅ Values valid")
        
        # Check 4: Pydantic validation
        print("\n🔍 Check 4: Schema validation")
        try:
            DemoSummary(**summary_data)
            results["schema"] = {"valid": True}
            print(f"   ✅ Schema valid")
        except ValidationError as e:
            results["schema"] = {"valid": False, "errors": str(e)}
            print(f"   ❌ Schema invalid: {e}")
        
        # Final result
        all_valid = all(r.get("valid", False) for r in results.values())
        
        print("\n" + "="*70)
        if all_valid:
            print("✅ SUMMARY VALIDATION: PASSED")
        else:
            print("⚠️ SUMMARY VALIDATION: FAILED")
        print("="*70)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "valid": all_valid,
            "checks": results
        }
    
    def create_demo_summary(self) -> DemoSummary:
        """Create a demo summary for testing."""
        return DemoSummary(
            incident_id="DEMO_001",
            timestamp=datetime.now().isoformat(),
            verdict="DANGEROUS",
            verdict_icon="🔴",
            risk_score=98,
            caller_number="+1555******7",
            victim_number="+9198******10",
            primary_reason="OTP request detected with urgent language",
            indicators=["otp_request", "urgent_action", "bank_impersonation"],
            transcript_excerpt="Your account is compromised. Share the OTP...",
            evidence_hash="a1b2c3d4e5f67890",
            action_taken="BLOCKED + Hold Music"
        )
    
    def print_demo_summary(self, summary: DemoSummary):
        """Print formatted demo summary."""
        print("\n" + "="*70)
        print(f"{summary.verdict_icon} DEMO INCIDENT SUMMARY")
        print("="*70)
        print(f"\n📋 Incident: {summary.incident_id}")
        print(f"🕐 Time: {summary.timestamp}")
        print(f"\n🎯 VERDICT: {summary.verdict_icon} {summary.verdict}")
        print(f"📊 Risk Score: {summary.risk_score}/100")
        print(f"\n📞 Caller: {summary.caller_number}")
        print(f"👤 Victim: {summary.victim_number}")
        print(f"\n🔍 Reason: {summary.primary_reason}")
        print(f"📝 Indicators: {', '.join(summary.indicators)}")
        print(f"\n📝 Transcript: \"{summary.transcript_excerpt}\"")
        print(f"\n🔒 Evidence Hash: {summary.evidence_hash}")
        print(f"✅ Action: {summary.action_taken}")
        print("\n" + "="*70)


if __name__ == "__main__":
    validator = SummaryValidator()
    
    # Create demo summary
    summary = validator.create_demo_summary()
    
    # Print it
    validator.print_demo_summary(summary)
    
    # Validate it
    result = validator.validate_summary(summary.model_dump())
    
    print(f"\n✅ Hour 22: Summary validator ready")
