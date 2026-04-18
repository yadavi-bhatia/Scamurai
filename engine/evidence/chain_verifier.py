
"""Hour 17: Tamper-Evident Verification - Chain integrity checking."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import hashlib


class ChainVerifier:
    """Verify tamper-evident chain integrity."""
    
    def __init__(self, chain_path: str = "data/immutable_log.jsonl"):
        self.chain_path = Path(chain_path)
    
    def verify_full_chain(self) -> Dict[str, Any]:
        """Verify the entire chain integrity."""
        if not self.chain_path.exists():
            return {"valid": True, "message": "No chain found", "entries": 0}
        
        entries = []
        with open(self.chain_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        if not entries:
            return {"valid": True, "message": "Empty chain", "entries": 0}
        
        for i, entry in enumerate(entries):
            entry_copy = entry.copy()
            stored_hash = entry_copy.pop('hash', None)
            content = json.dumps(entry_copy, sort_keys=True, default=str)
            computed_hash = hashlib.sha256(content.encode()).hexdigest()
            
            if stored_hash != computed_hash:
                return {"valid": False, "broken_at": i, "reason": "Hash mismatch"}
            
            if i > 0 and entry.get('prev_hash') != entries[i-1].get('hash'):
                return {"valid": False, "broken_at": i, "reason": "Chain broken"}
        
        return {
            "valid": True,
            "entries": len(entries),
            "last_hash": entries[-1].get('hash', '')[:16] if entries else ''
        }
    
    def generate_integrity_report(self) -> str:
        """Generate integrity report."""
        result = self.verify_full_chain()
        
        report = f"""
{'='*60}
TAMPER-EVIDENT CHAIN INTEGRITY REPORT
{'='*60}
Timestamp: {datetime.now().isoformat()}

Status: {'✅ INTACT' if result.get('valid') else '❌ COMPROMISED'}
Entries: {result.get('entries', 0)}
Last Hash: {result.get('last_hash', 'N/A')}
{'='*60}
"""
        return report


if __name__ == "__main__":
    print("✅ Hour 17: chain_verifier.py ready")
