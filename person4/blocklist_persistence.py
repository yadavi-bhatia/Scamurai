
"""Hour 25: Blocklist Persistence - Store spam numbers immediately after verdict."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import re


class BlocklistPersistence:
    """
    Persistent blocklist storage.
    Spam numbers are stored immediately after verdict.
    """
    
    def __init__(self, storage_path: str = "data/persistent_blocklist.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Load blocklist data from persistent storage."""
        if not self.storage_path.exists():
            self.data = {
                "version": "2.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_blocks": 0,
                "blocks": []  # List of all blocks
            }
        else:
            with open(self.storage_path, 'r') as f:
                self.data = json.load(f)
    
    def _save_data(self):
        """Save blocklist data to persistent storage."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _normalize_number(self, phone_number: str) -> str:
        """Normalize phone number for consistent storage."""
        return re.sub(r'[\s\-\(\)\+]', '', phone_number)
    
    def add_block(self, phone_number: str, reason: str, verdict: str, risk_score: float, 
                  user_id: str = "default_user", tags: List[str] = None) -> Dict[str, Any]:
        """
        Add a number to blocklist IMMEDIATELY after verdict.
        This is called right when scam is detected.
        """
        phone_number = self._normalize_number(phone_number)
        
        # Check if already blocked
        if self.is_blocked(phone_number, user_id):
            return {"status": "already_blocked", "phone_number": phone_number}
        
        block_entry = {
            "block_id": f"blk_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "phone_number": phone_number,
            "user_id": user_id,
            "reason": reason,
            "verdict": verdict,
            "risk_score": risk_score,
            "tags": tags or [],
            "blocked_at": datetime.now().isoformat(),
            "source": "auto_detection",
            "active": True
        }
        
        self.data["blocks"].append(block_entry)
        self.data["total_blocks"] += 1
        self._save_data()
        
        return {
            "status": "blocked",
            "phone_number": phone_number,
            "block_id": block_entry["block_id"],
            "blocked_at": block_entry["blocked_at"]
        }
    
    def is_blocked(self, phone_number: str, user_id: str = "default_user") -> bool:
        """Check if a number is blocked."""
        phone_number = self._normalize_number(phone_number)
        for block in self.data["blocks"]:
            if (block["phone_number"] == phone_number and 
                block["user_id"] == user_id and 
                block.get("active", True)):
                return True
        return False
    
    def remove_block(self, phone_number: str, user_id: str = "default_user", reason: str = "User request") -> bool:
        """Remove a number from blocklist (soft delete)."""
        phone_number = self._normalize_number(phone_number)
        for block in self.data["blocks"]:
            if block["phone_number"] == phone_number and block["user_id"] == user_id:
                block["active"] = False
                block["unblocked_at"] = datetime.now().isoformat()
                block["unblock_reason"] = reason
                self._save_data()
                return True
        return False
    
    def get_blocked_numbers(self, user_id: str = "default_user") -> List[Dict]:
        """Get all actively blocked numbers for a user."""
        return [
            b for b in self.data["blocks"]
            if b["user_id"] == user_id and b.get("active", True)
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get blocklist statistics."""
        active_blocks = sum(1 for b in self.data["blocks"] if b.get("active", True))
        return {
            "total_blocks_recorded": self.data["total_blocks"],
            "active_blocks": active_blocks,
            "total_users": len(set(b["user_id"] for b in self.data["blocks"])),
            "created_at": self.data["created_at"],
            "last_updated": self.data["last_updated"]
        }
    
    def get_block_history(self, phone_number: str) -> List[Dict]:
        """Get block history for a specific number."""
        phone_number = self._normalize_number(phone_number)
        return [b for b in self.data["blocks"] if b["phone_number"] == phone_number]


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 25: Blocklist Persistence")
    print("="*50)
    
    storage = BlocklistPersistence("data/test_blocklist.json")
    
    # Add a block immediately
    result = storage.add_block("+15551234567", "Scam detected - OTP request", "DANGEROUS", 95)
    print(f"✅ Block added: {result}")
    
    # Check if blocked
    is_blocked = storage.is_blocked("+15551234567")
    print(f"✅ Is blocked: {is_blocked}")
    
    # Get statistics
    stats = storage.get_statistics()
    print(f"✅ Statistics: {stats}")
    
    print("\n✅ Hour 25 Complete: Blocklist persistence ready!")
