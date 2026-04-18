
"""Hour 14: Decision Logger - Connect decision output to logs."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json


class DecisionLogger:
    """Log final decisions with evidence."""
    
    def __init__(self, storage_path: str = "data/decisions.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._decisions: List[Dict] = []
        self._load_decisions()
    
    def _load_decisions(self):
        if not self.storage_path.exists():
            return
        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    self._decisions.append(json.loads(line))
    
    def log_decision(
        self,
        call_id: str,
        verdict: str,
        score: float,
        reason: str,
        evidence: Dict[str, Any],
        incident_hash: str = "",
        chain_position: int = 0
    ) -> Dict[str, Any]:
        decision_record = {
            "decision_id": f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().isoformat(),
            "call_id": call_id,
            "verdict": verdict,
            "risk_score": score,
            "decision_reason": reason,
            "evidence": evidence,
            "incident_hash": incident_hash,
            "chain_position": chain_position
        }
        self._decisions.append(decision_record)
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(decision_record) + '\n')
        print(f"✅ Decision logged for call: {call_id} - {verdict}")
        return decision_record
    
    def get_decision(self, call_id: str) -> Optional[Dict]:
        for decision in reversed(self._decisions):
            if decision.get('call_id') == call_id:
                return decision
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self._decisions:
            return {"total": 0}
        verdict_counts = {}
        for d in self._decisions:
            v = d.get('verdict', 'UNKNOWN')
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
        return {
            "total": len(self._decisions),
            "verdict_distribution": verdict_counts,
            "average_score": sum(d.get('risk_score', 0) for d in self._decisions) / len(self._decisions)
        }


if __name__ == "__main__":
    print("✅ Hour 14: decision_logger.py ready")
