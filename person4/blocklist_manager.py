
"""Blocklist Manager - Local user blocklist."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import re


class BlocklistManager:
    def __init__(self, storage_path: str = "data/blocklist.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.blocklist_data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return {"users": {}, "total_blocks": 0}
        with open(self.storage_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.blocklist_data, f, indent=2)
    
    def _normalize(self, num: str) -> str:
        return re.sub(r'[\s\-\(\)\+]', '', num)
    
    def block_number(self, user_id: str, phone_number: str, reason: str, verdict: str = "DANGEROUS", risk_score: float = 0) -> Dict:
        phone_number = self._normalize(phone_number)
        
        if user_id not in self.blocklist_data["users"]:
            self.blocklist_data["users"][user_id] = {"blocked_numbers": {}, "whitelist": {}}
        
        entry = {
            "phone_number": phone_number,
            "blocked_at": datetime.now().isoformat(),
            "reason": reason,
            "verdict": verdict,
            "risk_score": risk_score
        }
        
        self.blocklist_data["users"][user_id]["blocked_numbers"][phone_number] = entry
        self.blocklist_data["total_blocks"] += 1
        self._save_data()
        
        return {"status": "blocked", "phone_number": phone_number}
    
    def is_blocked(self, user_id: str, phone_number: str) -> bool:
        phone_number = self._normalize(phone_number)
        if user_id in self.blocklist_data["users"]:
            return phone_number in self.blocklist_data["users"][user_id]["blocked_numbers"]
        return False
    
    def add_whitelist(self, user_id: str, phone_number: str, name: str) -> Dict:
        phone_number = self._normalize(phone_number)
        if user_id not in self.blocklist_data["users"]:
            self.blocklist_data["users"][user_id] = {"blocked_numbers": {}, "whitelist": {}}
        
        self.blocklist_data["users"][user_id]["whitelist"][phone_number] = {"name": name, "added_at": datetime.now().isoformat()}
        self._save_data()
        return {"status": "whitelisted", "phone_number": phone_number}
    
    def get_statistics(self) -> Dict:
        return {
            "total_blocks": self.blocklist_data["total_blocks"],
            "total_users": len(self.blocklist_data["users"])
        }


print("✅ blocklist_manager.py ready")
