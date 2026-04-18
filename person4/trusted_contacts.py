
"""Trusted Contacts - Emergency alert sharing."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class TrustedContactsManager:
    def __init__(self, storage_path: str = "data/trusted_contacts.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.contacts_data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return {"users": {}, "total_alerts_sent": 0}
        with open(self.storage_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.contacts_data, f, indent=2)
    
    def add_contact(self, user_id: str, name: str, phone_number: str, relationship: str = "friend") -> Dict:
        if user_id not in self.contacts_data["users"]:
            self.contacts_data["users"][user_id] = {"contacts": [], "alert_history": []}
        
        contact = {
            "id": f"c_{len(self.contacts_data['users'][user_id]['contacts'])}",
            "name": name,
            "phone_number": phone_number,
            "relationship": relationship,
            "added_at": datetime.now().isoformat(),
            "alert_count": 0
        }
        
        self.contacts_data["users"][user_id]["contacts"].append(contact)
        self._save_data()
        return contact
    
    def get_contacts(self, user_id: str) -> List[Dict]:
        if user_id not in self.contacts_data["users"]:
            return []
        return self.contacts_data["users"][user_id]["contacts"]
    
    def send_alert(self, user_id: str, contact_ids: List[str], alert_data: Dict) -> Dict:
        contacts = self.get_contacts(user_id)
        selected = [c for c in contacts if c["id"] in contact_ids]
        
        caller = alert_data.get("caller_number", "Unknown")
        category = alert_data.get("scam_category", "Scam")
        reason = alert_data.get("reason", "Suspicious call")
        
        message = f"""🚨 POSSIBLE SCAM ALERT!
Caller: {caller}
Type: {category}
Reason: {reason}
Time: {datetime.now().strftime('%I:%M %p')}"""
        
        alert = {
            "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "contacts": selected,
            "message": message
        }
        
        self.contacts_data["total_alerts_sent"] += 1
        self._save_data()
        
        return {"alert_id": alert["alert_id"], "message": message, "contacts": len(selected)}
    
    def get_statistics(self) -> Dict:
        total_contacts = sum(len(u.get("contacts", [])) for u in self.contacts_data["users"].values())
        return {
            "total_alerts_sent": self.contacts_data["total_alerts_sent"],
            "total_contacts": total_contacts,
            "total_users": len(self.contacts_data["users"])
        }


print("✅ trusted_contacts.py ready")
