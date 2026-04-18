
"""Shared Reputation List - Community spam reporting."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import re


class ReputationManager:
    def __init__(self, storage_path: str = "data/reputation.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.reputation_data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "total_numbers": 0,
                "total_reports": 0,
                "numbers": {}
            }
        with open(self.storage_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.reputation_data, f, indent=2)
    
    def _normalize_number(self, phone_number: str) -> str:
        return re.sub(r'[\s\-\(\)\+]', '', phone_number)
    
    def add_report(self, phone_number: str, verdict: str, tags: List[str], 
                   confidence: float, source: str = "system", user_id: str = None) -> Dict[str, Any]:
        phone_number = self._normalize_number(phone_number)
        
        if phone_number not in self.reputation_data["numbers"]:
            self.reputation_data["numbers"][phone_number] = {
                "first_reported": datetime.now().isoformat(),
                "total_reports": 0,
                "reports": [],
                "current_score": 0,
                "tags": {}
            }
        
        num_data = self.reputation_data["numbers"][phone_number]
        
        report = {
            "report_id": f"rpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "verdict": verdict,
            "tags": tags,
            "confidence": confidence,
            "source": source
        }
        
        num_data["reports"].append(report)
        num_data["total_reports"] += 1
        
        for tag in tags:
            num_data["tags"][tag] = num_data["tags"].get(tag, 0) + 1
        
        num_data["current_score"] = min(len(num_data["reports"]) * 10 + int(confidence * 30), 100)
        
        self.reputation_data["total_numbers"] = len(self.reputation_data["numbers"])
        self.reputation_data["total_reports"] += 1
        self._save_data()
        
        return {"phone_number": phone_number, "reputation_score": num_data["current_score"]}
    
    def get_reputation(self, phone_number: str) -> Dict[str, Any]:
        phone_number = self._normalize_number(phone_number)
        if phone_number not in self.reputation_data["numbers"]:
            return {"phone_number": phone_number, "exists": False, "reputation_score": 0}
        
        num_data = self.reputation_data["numbers"][phone_number]
        return {
            "phone_number": phone_number,
            "exists": True,
            "reputation_score": num_data["current_score"],
            "total_reports": num_data["total_reports"],
            "first_reported": num_data["first_reported"]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        risk_dist = {"high": 0, "medium": 0, "low": 0}
        for data in self.reputation_data["numbers"].values():
            s = data["current_score"]
            if s >= 70: risk_dist["high"] += 1
            elif s >= 40: risk_dist["medium"] += 1
            else: risk_dist["low"] += 1
        
        return {
            "total_numbers": self.reputation_data["total_numbers"],
            "total_reports": self.reputation_data["total_reports"],
            "risk_distribution": risk_dist
        }


print("✅ reputation_manager.py ready")
