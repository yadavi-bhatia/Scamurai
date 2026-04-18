"""
Person 2 - Evidence Builder
Builds tamper-proof evidence records for forensic use
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import config


@dataclass
class EvidenceRecord:
    """Single evidence record for a turn"""
    turn_id: str
    session_id: str
    timestamp: str
    transcript: str
    risk_score: float
    risk_level: str
    detected_keywords: List[str]
    detected_categories: List[str]
    evidence_hash: str
    previous_hash: str
    audio_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class EvidenceBuilder:
    """
    Builds and manages tamper-proof evidence chain
    Uses SHA-256 hashing for integrity verification
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.evidence_chain: List[EvidenceRecord] = []
        self.last_hash = "0" * 64  # Genesis hash
        self.output_dir = config.EVIDENCE_CONFIG["output_dir"]
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/{session_id}", exist_ok=True)
        
        print(f"📁 Evidence Builder initialized for session: {session_id}")
    
    def add_evidence(self, 
                     turn_id: str,
                     transcript: str,
                     risk_score: float,
                     risk_level: str,
                     detected_keywords: List[str],
                     detected_categories: List[str],
                     audio_hash: Optional[str] = None) -> EvidenceRecord:
        """
        Add a new evidence record to the chain
        """
        # Create evidence string for hashing
        evidence_string = f"{turn_id}|{self.session_id}|{transcript}|{risk_score}|{datetime.now().isoformat()}|{self.last_hash}"
        
        # Generate hash
        current_hash = hashlib.sha256(evidence_string.encode()).hexdigest()
        
        # Create record
        record = EvidenceRecord(
            turn_id=turn_id,
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            transcript=transcript[:500],
            risk_score=risk_score,
            risk_level=risk_level,
            detected_keywords=detected_keywords[:10],
            detected_categories=detected_categories,
            evidence_hash=current_hash,
            previous_hash=self.last_hash,
            audio_hash=audio_hash
        )
        
        # Add to chain
        self.evidence_chain.append(record)
        self.last_hash = current_hash
        
        # Save to disk (only high risk if configured)
        should_save = True
        if config.EVIDENCE_CONFIG.get("save_high_risk_only", True):
            should_save = risk_score >= config.RISK_THRESHOLDS["medium"]
        
        if should_save:
            self._save_evidence(record)
        
        return record
    
    def _save_evidence(self, record: EvidenceRecord):
        """Save evidence record to disk"""
        file_path = f"{self.output_dir}/{self.session_id}/{record.turn_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(record.to_json())
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the evidence chain
        Returns verification result
        """
        if not self.evidence_chain:
            return {"verified": True, "message": "No evidence in chain"}
        
        previous_hash = "0" * 64
        verified = True
        broken_at = None
        
        for i, record in enumerate(self.evidence_chain):
            # Recompute hash
            evidence_string = f"{record.turn_id}|{record.session_id}|{record.transcript}|{record.risk_score}|{record.timestamp}|{previous_hash}"
            computed_hash = hashlib.sha256(evidence_string.encode()).hexdigest()
            
            if computed_hash != record.evidence_hash:
                verified = False
                broken_at = i
                break
            
            previous_hash = record.evidence_hash
        
        return {
            "verified": verified,
            "total_records": len(self.evidence_chain),
            "broken_at_index": broken_at,
            "last_hash": self.last_hash,
            "session_id": self.session_id
        }
    
    def get_session_report(self) -> Dict[str, Any]:
        """
        Generate complete session report with all evidence
        """
        if not self.evidence_chain:
            return {"error": "No evidence for this session"}
        
        max_risk = max([r.risk_score for r in self.evidence_chain])
        total_keywords = set()
        total_categories = set()
        
        for r in self.evidence_chain:
            total_keywords.update(r.detected_keywords)
            total_categories.update(r.detected_categories)
        
        # Determine final verdict
        if max_risk >= config.RISK_THRESHOLDS["critical"]:
            verdict = "SCAM_CONFIRMED"
            severity = "CRITICAL"
        elif max_risk >= config.RISK_THRESHOLDS["high"]:
            verdict = "SCAM_LIKELY"
            severity = "HIGH"
        elif max_risk >= config.RISK_THRESHOLDS["medium"]:
            verdict = "SUSPICIOUS"
            severity = "MEDIUM"
        else:
            verdict = "LOW_RISK"
            severity = "LOW"
        
        return {
            "session_id": self.session_id,
            "total_turns": len(self.evidence_chain),
            "max_risk_score": round(max_risk, 3),
            "final_verdict": verdict,
            "severity": severity,
            "unique_keywords_detected": list(total_keywords)[:20],
            "categories_detected": list(total_categories),
            "chain_verified": self.verify_chain()["verified"],
            "report_generated": datetime.now().isoformat()
        }
    
    def export_evidence(self, format: str = "json") -> str:
        """
        Export all evidence in specified format
        Formats: json, csv, html
        """
        if format == "json":
            return json.dumps([r.to_dict() for r in self.evidence_chain], indent=2)
        
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if self.evidence_chain:
                writer = csv.DictWriter(output, fieldnames=self.evidence_chain[0].to_dict().keys())
                writer.writeheader()
                for record in self.evidence_chain:
                    writer.writerow(record.to_dict())
            return output.getvalue()
        
        elif format == "html":
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Evidence Report - Session {session_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .critical {{ background-color: #ff4444; color: white; padding: 10px; }}
                    .high {{ background-color: #ff8800; padding: 10px; }}
                    .medium {{ background-color: #ffcc00; padding: 10px; }}
                    .low {{ background-color: #44ff44; padding: 10px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Evidence Report</h1>
                <p>Session: {session_id}</p>
                <p>Generated: {timestamp}</p>
                <table>
                    <tr>
                        <th>Turn ID</th>
                        <th>Timestamp</th>
                        <th>Transcript</th>
                        <th>Risk Score</th>
                        <th>Risk Level</th>
                        <th>Keywords</th>
                    </tr>
            """.format(session_id=self.session_id, timestamp=datetime.now().isoformat())
            
            for record in self.evidence_chain:
                risk_class = "low"
                if record.risk_score >= 0.65:
                    risk_class = "critical"
                elif record.risk_score >= 0.45:
                    risk_class = "high"
                elif record.risk_score >= 0.25:
                    risk_class = "medium"
                
                html += f"""
                    <tr class="{risk_class}">
                        <td>{record.turn_id}</td>
                        <td>{record.timestamp}</td>
                        <td>{record.transcript[:100]}</td>
                        <td>{record.risk_score:.0%}</td>
                        <td>{record.risk_level}</td>
                        <td>{', '.join(record.detected_keywords[:5])}</td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            return html
        
        return json.dumps({"error": f"Unsupported format: {format}"})
    
    def clear(self):
        """Clear all evidence for this session"""
        self.evidence_chain = []
        self.last_hash = "0" * 64
        print(f"🗑️ Evidence cleared for session: {self.session_id}")


# Quick test
if __name__ == "__main__":
    builder = EvidenceBuilder("test_session_001")
    
    # Add some evidence
    record1 = builder.add_evidence(
        turn_id="T001",
        transcript="Send me bitcoin immediately",
        risk_score=0.65,
        risk_level="HIGH",
        detected_keywords=["bitcoin", "immediately"],
        detected_categories=["payment_request", "urgency"]
    )
    
    record2 = builder.add_evidence(
        turn_id="T002",
        transcript="Your social security number is compromised",
        risk_score=0.70,
        risk_level="CRITICAL",
        detected_keywords=["social security", "compromised"],
        detected_categories=["identity_theft", "scam_phrases"]
    )
    
    # Verify chain
    verification = builder.verify_chain()
    print(f"Chain verified: {verification['verified']}")
    
    # Get report
    report = builder.get_session_report()
    print("\nSession Report:")
    print(json.dumps(report, indent=2))
    
    # Export HTML
    html_report = builder.export_evidence("html")
    with open("evidence_report.html", "w") as f:
        f.write(html_report)
    print("\n✅ HTML report saved to evidence_report.html")