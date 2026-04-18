
"""Hour 13: Immutable Logger - Save metadata with cryptographic hashes."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import hashlib


class ImmutableLogger:
    """Immutable log entries with cryptographic hashes."""
    
    def __init__(self, log_path: str = "data/immutable_log.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[Dict] = []
        self._load_entries()
    
    def _load_entries(self):
        if not self.log_path.exists():
            return
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    self._entries.append(json.loads(line))
    
    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        entry_copy = entry.copy()
        entry_copy.pop('hash', None)
        entry_copy.pop('prev_hash', None)
        content = json.dumps(entry_copy, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def log_entry(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if self._entries:
            prev_hash = self._entries[-1].get('hash', 'GENESIS')
        else:
            prev_hash = hashlib.sha256(b"GENESIS").hexdigest()
        
        entry = {
            "index": len(self._entries),
            "timestamp": datetime.now().isoformat(),
            "prev_hash": prev_hash,
            "metadata": metadata,
            "hash": ""
        }
        entry["hash"] = self._calculate_hash(entry)
        self._entries.append(entry)
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        print(f"🔒 Immutable entry #{entry['index']} logged")
        return entry
    
    def verify_all(self) -> Dict[str, Any]:
        for i, entry in enumerate(self._entries):
            computed = self._calculate_hash(entry)
            if entry['hash'] != computed:
                return {"valid": False, "broken_at": i}
            if i > 0 and entry['prev_hash'] != self._entries[i-1]['hash']:
                return {"valid": False, "broken_at": i}
        return {"valid": True, "total_entries": len(self._entries)}


if __name__ == "__main__":
    print("✅ Hour 13: immutable_logger.py ready")
