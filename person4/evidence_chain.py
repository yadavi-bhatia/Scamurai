
"""Evidence Chain - Tamper-evident logging."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import hashlib
import json
from pathlib import Path


class EvidenceBlock(BaseModel):
    """Single block in evidence chain."""
    index: int
    timestamp: datetime
    prev_hash: str
    evidence: Dict[str, Any]
    hash: str = ""


class EvidenceChain:
    """Append-only, tamper-evident chain."""
    
    def __init__(self, storage_path: str = "data/evidence_chain.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._chain: List[EvidenceBlock] = []
        self._load()
    
    def _load(self):
        if not self.storage_path.exists():
            return
        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    self._chain.append(EvidenceBlock(**json.loads(line)))
    
    def append(self, evidence: Dict[str, Any]) -> EvidenceBlock:
        """Append new evidence (APPEND ONLY)."""
        
        prev_hash = self._chain[-1].hash if self._chain else hashlib.sha256(b"GENESIS").hexdigest()
        
        block = EvidenceBlock(
            index=len(self._chain),
            timestamp=datetime.now(),
            prev_hash=prev_hash,
            evidence=evidence
        )
        
        # Calculate hash
        block_dict = block.model_dump(exclude={'hash'})
        block.hash = hashlib.sha256(
            json.dumps(block_dict, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        self._chain.append(block)
        
        with open(self.storage_path, 'a') as f:
            f.write(block.model_dump_json() + '\n')
        
        return block
    
    def verify(self) -> Dict[str, Any]:
        """Verify chain integrity."""
        for i, block in enumerate(self._chain):
            block_dict = block.model_dump(exclude={'hash'})
            computed = hashlib.sha256(
                json.dumps(block_dict, sort_keys=True, default=str).encode()
            ).hexdigest()
            
            if block.hash != computed:
                return {"valid": False, "broken_at": i, "reason": "Hash mismatch"}
            
            if i > 0 and block.prev_hash != self._chain[i-1].hash:
                return {"valid": False, "broken_at": i, "reason": "Chain broken"}
        
        return {"valid": True, "length": len(self._chain)}
    
    def get_chain(self) -> List[EvidenceBlock]:
        return self._chain.copy()
    
    def get_latest(self) -> Optional[EvidenceBlock]:
        return self._chain[-1] if self._chain else None
