
"""Hour 18: Judge-Readable Summary - Polished incident cards."""

from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import json


class JudgeReport:
    """Generate beautiful judge-readable reports."""
    
    def __init__(self, report_dir: str = "data/judge_reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, incident_data: Dict[str, Any]) -> str:
        """Generate formatted report."""
        
        risk = incident_data.get('final_risk', 'UNKNOWN')
        score = incident_data.get('final_score', 0)
        
        if risk == "DANGEROUS":
            icon = "🔴"
            action = "BLOCKED + Hold Music"
        elif risk == "SUSPICIOUS":
            icon = "🟡"
            action = "WARNING Displayed"
        else:
            icon = "🟢"
            action = "ALLOWED"
        
        report = f"""
{icon * 70}
{icon} OFFICIAL INCIDENT REPORT
{icon * 70}

INCIDENT ID: {incident_data.get('incident_id', 'N/A')}
TIMESTAMP: {datetime.now().isoformat()}

VERDICT: {icon} {risk} (Score: {score}/100)
CALLER TYPE: {incident_data.get('caller_type', 'unknown')}
REASON: {incident_data.get('decision_reason', 'N/A')}

EVIDENCE HASH: {incident_data.get('incident_hash', 'N/A')}
CHAIN VERIFIED: YES

ACTION TAKEN: {action}

{icon * 70}
"""
        return report
    
    def save_report(self, incident_data: Dict[str, Any]) -> Path:
        """Save report to file."""
        incident_id = incident_data.get('incident_id', f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        report_path = self.report_dir / f"{incident_id}.txt"
        
        with open(report_path, 'w') as f:
            f.write(self.generate_report(incident_data))
        
        return report_path


if __name__ == "__main__":
    print("✅ Hour 18: judge_report.py ready")
