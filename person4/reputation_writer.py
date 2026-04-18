
"""Hour 26: Reputation Writer - Add numbers to community spam list."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import re


class ReputationWriter:
    """
    Shared spam reputation list writer.
    Numbers can be added to community spam list immediately.
    """
    
    def __init__(self, storage_path: str = "data/community_spam.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Load reputation data."""
        if not self.storage_path.exists():
            self.data = {
                "version": "2.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_numbers": 0,
                "total_reports": 0,
                "numbers": {}
            }
        else:
            with open(self.storage_path, 'r') as f:
                self.data = json.load(f)
    
    def _save_data(self):
        """Save reputation data."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _normalize_number(self, phone_number: str) -> str:
        """Normalize phone number."""
        return re.sub(r'[\s\-\(\)\+]', '', phone_number)
    
    def add_to_community_list(
        self,
        phone_number: str,
        verdict: str,
        tags: List[str],
        confidence: float,
        source: str = "system",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a number to the community spam list.
        This builds the shared reputation database.
        """
        phone_number = self._normalize_number(phone_number)
        
        if phone_number not in self.data["numbers"]:
            self.data["numbers"][phone_number] = {
                "first_reported": datetime.now().isoformat(),
                "total_reports": 0,
                "reputation_score": 0,
                "reports": [],
                "tags": {},
                "verdicts": []
            }
        
        num_data = self.data["numbers"][phone_number]
        
        report = {
            "report_id": f"rpt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().isoformat(),
            "verdict": verdict,
            "tags": tags,
            "confidence": confidence,
            "source": source,
            "user_id": user_id
        }
        
        num_data["reports"].append(report)
        num_data["total_reports"] += 1
        num_data["verdicts"].append(verdict)
        
        # Update tag counts
        for tag in tags:
            num_data["tags"][tag] = num_data["tags"].get(tag, 0) + 1
        
        # Calculate reputation score
        base_score = min(num_data["total_reports"] * 10, 50)
        confidence_score = sum(r["confidence"] for r in num_data["reports"]) / len(num_data["reports"]) * 30
        num_data["reputation_score"] = min(base_score + confidence_score, 100)
        
        self.data["total_numbers"] = len(self.data["numbers"])
        self.data["total_reports"] += 1
        self._save_data()
        
        return {
            "phone_number": phone_number,
            "reputation_score": num_data["reputation_score"],
            "total_reports": num_data["total_reports"],
            "first_reported": num_data["first_reported"]
        }
    
    def get_reputation(self, phone_number: str) -> Dict[str, Any]:
        """Get reputation for a number."""
        phone_number = self._normalize_number(phone_number)
        
        if phone_number not in self.data["numbers"]:
            return {
                "phone_number": phone_number,
                "exists": False,
                "reputation_score": 0,
                "risk_level": "unknown"
            }
        
        num_data = self.data["numbers"][phone_number]
        score = num_data["reputation_score"]
        
        if score >= 70:
            risk_level = "high"
        elif score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "phone_number": phone_number,
            "exists": True,
            "reputation_score": score,
            "total_reports": num_data["total_reports"],
            "first_reported": num_data["first_reported"],
            "risk_level": risk_level,
            "top_tags": sorted(num_data["tags"].items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    def get_community_statistics(self) -> Dict[str, Any]:
        """Get community spam list statistics."""
        risk_dist = {"high": 0, "medium": 0, "low": 0}
        for num_data in self.data["numbers"].values():
            score = num_data["reputation_score"]
            if score >= 70:
                risk_dist["high"] += 1
            elif score >= 40:
                risk_dist["medium"] += 1
            else:
                risk_dist["low"] += 1
        
        return {
            "total_numbers_in_community_list": self.data["total_numbers"],
            "total_reports_submitted": self.data["total_reports"],
            "risk_distribution": risk_dist,
            "created_at": self.data["created_at"],
            "last_updated": self.data["last_updated"]
        }
    
    def get_top_reported(self, limit: int = 10) -> List[Dict]:
        """Get top reported numbers."""
        numbers = []
        for number, data in self.data["numbers"].items():
            numbers.append({
                "phone_number": number,
                "reputation_score": data["reputation_score"],
                "total_reports": data["total_reports"]
            })
        numbers.sort(key=lambda x: x["reputation_score"], reverse=True)
        return numbers[:limit]


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 26: Reputation Writer")
    print("="*50)
    
    writer = ReputationWriter("data/test_community.json")
    
    # Add to community list
    result = writer.add_to_community_list("+15551234567", "DANGEROUS", ["otp_request", "bank_fraud"], 0.95)
    print(f"✅ Added to community list: {result}")
    
    # Add another report
    writer.add_to_community_list("+15551234567", "DANGEROUS", ["impersonation"], 0.90, "user", "user_001")
    
    # Get reputation
    rep = writer.get_reputation("+15551234567")
    print(f"✅ Reputation: {rep}")
    
    # Get statistics
    stats = writer.get_community_statistics()
    print(f"✅ Community statistics: {stats}")
    
    print("\n✅ Hour 26 Complete: Reputation writer ready!")
