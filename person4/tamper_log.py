"""Tamper-evident logging with SHA-256 hash chain."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class TamperEvidentLog:
    """Append-only log with hash chain verification."""
    
    def __init__(self, log_path: Optional[str] = None):  # Changed: str → Optional[str]
        """Initialize the tamper-evident log.
        
        Args:
            log_path: Optional path to log file. If None, uses default location.
        """
        if log_path is None:
            # This creates: /path/to/Scamurai/person4/data/logs/audit_chain.log
            self.log_path = Path(__file__).parent / "data" / "logs" / "audit_chain.log"
        else:
            self.log_path = Path(log_path)
        
        # Create directory if it doesn't exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._get_last_hash()
    
    def _get_last_hash(self) -> str:
        """Get the hash of the last record."""
        if not self.log_path.exists():
            return hashlib.sha256(b"GENESIS").hexdigest()
        
        try:
            with open(self.log_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = json.loads(lines[-1])
                    return last_line.get('hash', hashlib.sha256(b"GENESIS").hexdigest())
        except Exception:
            pass
        
        return hashlib.sha256(b"GENESIS").hexdigest()
    
    def append(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Append a new incident to the log."""
        
        # Create record with prev_hash
        record = {
            "timestamp": datetime.now().isoformat(),
            "prev_hash": self._last_hash,
            **decision_data
        }
        
        # Compute hash for this record
        record_json = json.dumps(record, sort_keys=True, default=str)
        record["hash"] = hashlib.sha256(record_json.encode()).hexdigest()
        
        # Append to file
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        self._last_hash = record["hash"]
        
        # Print confirmation (for debugging)
        print(f"📝 Log written to: {self.log_path}")
        
        return record
    
    def verify_chain(self) -> tuple[bool, List[str]]:
        """Verify the entire log chain."""
        if not self.log_path.exists():
            return True, ["Log is empty"]
        
        errors = []
        prev_hash = hashlib.sha256(b"GENESIS").hexdigest()
        
        with open(self.log_path, 'r') as f:
            for line_num, line in enumerate(f):
                try:
                    record = json.loads(line)
                    
                    if record.get('prev_hash') != prev_hash:
                        errors.append(f"Line {line_num}: prev_hash mismatch")
                    
                    # Verify hash
                    record_copy = record.copy()
                    record_hash = record_copy.pop('hash')
                    record_json = json.dumps(record_copy, sort_keys=True, default=str)
                    computed_hash = hashlib.sha256(record_json.encode()).hexdigest()
                    
                    if record_hash != computed_hash:
                        errors.append(f"Line {line_num}: hash mismatch")
                    
                    prev_hash = record_hash
                    
                except Exception as e:
                    errors.append(f"Line {line_num}: parse error - {e}")
        
        return len(errors) == 0, errors
    
    def get_all_records(self) -> List[Dict]:
        """Retrieve all records."""
        records = []
        if not self.log_path.exists():
            return records
        
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        return records