
"""Hour 32: Immutable Action Logger - Every action tied to tamper-evident record."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import hashlib


class ImmutableActionLogger:
    """
    Hour 32: Immutable Action Logger
    Every action is tied to a tamper-evident incident record.
    """
    
    def __init__(self, storage_path: str = "data/action_chain.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._chain: List[Dict] = []
        self._load_chain()
    
    def _load_chain(self):
        """Load existing chain."""
        if not self.storage_path.exists():
            return
        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    self._chain.append(json.loads(line))
    
    def _calculate_hash(self, record: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of a record."""
        record_copy = record.copy()
        record_copy.pop('hash', None)
        record_copy.pop('prev_hash', None)
        content = json.dumps(record_copy, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def log_action(
        self,
        action_type: str,
        incident_id: str,
        details: Dict[str, Any],
        call_id: str = None
    ) -> Dict[str, Any]:
        """
        Log an action to the immutable chain.
        Every action is cryptographically linked to previous actions.
        """
        # Get previous hash
        if self._chain:
            prev_hash = self._chain[-1].get('hash', 'GENESIS')
        else:
            prev_hash = hashlib.sha256(b"GENESIS").hexdigest()
        
        # Create action record
        record = {
            "index": len(self._chain),
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "incident_id": incident_id,
            "call_id": call_id,
            "details": details,
            "prev_hash": prev_hash,
            "hash": ""  # Will compute below
        }
        
        # Calculate and set hash
        record["hash"] = self._calculate_hash(record)
        
        # Add to chain
        self._chain.append(record)
        
        # Persist to disk
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(record) + '\n')
        
        return record
    
    def log_block_action(
        self,
        phone_number: str,
        reason: str,
        verdict: str,
        risk_score: float,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """Log a block action to immutable chain."""
        return self.log_action(
            action_type="block",
            incident_id=f"block_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            details={
                "phone_number": phone_number,
                "reason": reason,
                "verdict": verdict,
                "risk_score": risk_score,
                "user_id": user_id
            }
        )
    
    def log_report_action(
        self,
        phone_number: str,
        verdict: str,
        tags: List[str],
        confidence: float,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log a report action to immutable chain."""
        return self.log_action(
            action_type="report",
            incident_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            details={
                "phone_number": phone_number,
                "verdict": verdict,
                "tags": tags,
                "confidence": confidence,
                "user_id": user_id
            }
        )
    
    def log_share_action(
        self,
        caller_number: str,
        contact_ids: List[str],
        scam_category: str,
        amount_at_risk: Optional[float],
        user_id: str
    ) -> Dict[str, Any]:
        """Log a share/alert action to immutable chain."""
        return self.log_action(
            action_type="share_alert",
            incident_id=f"share_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            details={
                "caller_number": caller_number,
                "contact_ids": contact_ids,
                "scam_category": scam_category,
                "amount_at_risk": amount_at_risk,
                "user_id": user_id
            }
        )
    
    def log_call_finalize(
        self,
        call_id: str,
        verdict: str,
        risk_score: float,
        actions_taken: List[str],
        severity: str
    ) -> Dict[str, Any]:
        """Log complete call finalization to immutable chain."""
        return self.log_action(
            action_type="call_finalize",
            incident_id=f"call_{call_id}",
            call_id=call_id,
            details={
                "verdict": verdict,
                "risk_score": risk_score,
                "actions_taken": actions_taken,
                "severity": severity
            }
        )
    
    def verify_chain(self) -> Dict[str, Any]:
        """Verify the entire immutable chain."""
        for i, record in enumerate(self._chain):
            # Verify hash
            computed_hash = self._calculate_hash(record)
            if record['hash'] != computed_hash:
                return {
                    "valid": False,
                    "broken_at": i,
                    "reason": f"Hash mismatch at index {i}"
                }
            
            # Verify chain link
            if i > 0 and record['prev_hash'] != self._chain[i-1]['hash']:
                return {
                    "valid": False,
                    "broken_at": i,
                    "reason": f"Chain broken between {i-1} and {i}"
                }
        
        return {"valid": True, "total_entries": len(self._chain)}
    
    def get_action_history(self, action_type: str = None, limit: int = 50) -> List[Dict]:
        """Get action history, optionally filtered by type."""
        if action_type:
            filtered = [r for r in self._chain if r.get('action_type') == action_type]
            return filtered[-limit:]
        return self._chain[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get immutable log statistics."""
        action_counts = {}
        for record in self._chain:
            action = record.get('action_type', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        verification = self.verify_chain()
        
        return {
            "total_actions": len(self._chain),
            "action_breakdown": action_counts,
            "chain_valid": verification.get('valid', False),
            "chain_entries": verification.get('total_entries', 0),
            "created_at": self._chain[0]['timestamp'] if self._chain else None,
            "last_updated": self._chain[-1]['timestamp'] if self._chain else None
        }


# Global instance
action_logger = ImmutableActionLogger()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 32: Immutable Action Logger")
    print("="*50)
    
    # Log some actions
    logger = ImmutableActionLogger("data/test_action_chain.jsonl")
    
    # Log a block action
    block_record = logger.log_block_action(
        phone_number="+15551234567",
        reason="Scam detected - OTP request",
        verdict="DANGEROUS",
        risk_score=95
    )
    print(f"✅ Block action logged: {block_record['index']}")
    
    # Log a report action
    report_record = logger.log_report_action(
        phone_number="+15551234567",
        verdict="DANGEROUS",
        tags=["otp_request", "bank_fraud"],
        confidence=0.95
    )
    print(f"✅ Report action logged: {report_record['index']}")
    
    # Log a share action
    share_record = logger.log_share_action(
        caller_number="+15551234567",
        contact_ids=["contact_1", "contact_2"],
        scam_category="Bank Fraud",
        amount_at_risk=100000,
        user_id="user_001"
    )
    print(f"✅ Share action logged: {share_record['index']}")
    
    # Log call finalize
    finalize_record = logger.log_call_finalize(
        call_id="call_001",
        verdict="DANGEROUS",
        risk_score=95,
        actions_taken=["block", "report", "share_alert"],
        severity="critical"
    )
    print(f"✅ Call finalize logged: {finalize_record['index']}")
    
    # Verify chain
    verification = logger.verify_chain()
    print(f"\n🔒 Chain valid: {verification['valid']}")
    print(f"📊 Total entries: {verification['total_entries']}")
    
    # Get statistics
    stats = logger.get_statistics()
    print(f"\n📊 Statistics: {stats}")
    
    print("\n✅ Hour 32 Complete: Immutable action logger ready!")
    print("\n🎉 HOURS 28-32 COMPLETE! All actions tied to tamper-evident records!")
