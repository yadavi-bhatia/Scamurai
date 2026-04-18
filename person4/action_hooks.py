
"""Hour 28: Action Hooks - Connect decision output to block, report, and share actions."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from action_schema import BlockAction, ReportAction, TrustedAlertAction, ActionResponse, ActionType
from blocklist_persistence import BlocklistPersistence
from reputation_writer import ReputationWriter
from alert_payload import TrustedAlertPayload, AlertPayloadFactory


@dataclass
class ActionHookResult:
    """Result from executing action hooks."""
    success: bool
    actions_executed: List[Dict[str, Any]]
    errors: List[str]
    summary: Dict[str, Any]


class ActionHooks:
    """
    Hour 28: Action Hooks
    Connects decision output to actual actions (block, report, share).
    """
    
    def __init__(self):
        self.blocklist_storage = BlocklistPersistence()
        self.reputation_writer = ReputationWriter()
        self.action_history: List[Dict] = []
    
    def execute_block_action(self, action: BlockAction) -> ActionResponse:
        """Execute block action - add number to blocklist."""
        try:
            result = self.blocklist_storage.add_block(
                phone_number=action.phone_number,
                reason=action.reason,
                verdict=action.verdict,
                risk_score=action.risk_score,
                user_id=action.user_id
            )
            
            self.action_history.append({
                "action_type": "block",
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            return ActionResponse(
                success=True,
                action_type=ActionType.BLOCK,
                message=f"Number {action.phone_number} blocked successfully",
                details=result
            )
        except Exception as e:
            return ActionResponse(
                success=False,
                action_type=ActionType.BLOCK,
                message=f"Failed to block number: {str(e)}",
                details={"error": str(e)}
            )
    
    def execute_report_action(self, action: ReportAction) -> ActionResponse:
        """Execute report action - add to community reputation list."""
        try:
            result = self.reputation_writer.add_to_community_list(
                phone_number=action.phone_number,
                verdict=action.verdict,
                tags=action.tags,
                confidence=action.confidence,
                source=action.source,
                user_id=action.user_id
            )
            
            self.action_history.append({
                "action_type": "report",
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            return ActionResponse(
                success=True,
                action_type=ActionType.REPORT,
                message=f"Number {action.phone_number} reported to community list",
                details=result
            )
        except Exception as e:
            return ActionResponse(
                success=False,
                action_type=ActionType.REPORT,
                message=f"Failed to report number: {str(e)}",
                details={"error": str(e)}
            )
    
    def execute_trusted_alert_action(self, action: TrustedAlertAction) -> ActionResponse:
        """Execute trusted alert action - send alert to contacts."""
        try:
            # Create alert payload
            alert_payload = TrustedAlertPayload(
                alert_id=f"alt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                caller_number=action.phone_number,
                scam_category=action.scam_category,
                reason=action.reason,
                amount_at_risk=action.amount_at_risk,
                time_of_call=datetime.now().strftime("%I:%M %p"),
                severity=action.severity
            )
            
            # Generate messages for different channels
            sms_message = alert_payload.to_sms_format()
            whatsapp_message = alert_payload.to_whatsapp_format()
            
            # In production, send via actual SMS/WhatsApp APIs
            # For demo, we just log and return
            result = {
                "alert_id": alert_payload.alert_id,
                "contacts": action.contact_ids,
                "sms_message": sms_message,
                "whatsapp_message": whatsapp_message,
                "sent_via": ["sms", "whatsapp"]
            }
            
            self.action_history.append({
                "action_type": "trusted_alert",
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            return ActionResponse(
                success=True,
                action_type=ActionType.TRUSTED_ALERT,
                message=f"Alert sent to {len(action.contact_ids)} trusted contacts",
                details=result
            )
        except Exception as e:
            return ActionResponse(
                success=False,
                action_type=ActionType.TRUSTED_ALERT,
                message=f"Failed to send alert: {str(e)}",
                details={"error": str(e)}
            )
    
    def execute_all_actions(
        self,
        call_id: str,
        caller_number: str,
        verdict: str,
        risk_score: float,
        reason: str,
        scam_tags: List[str],
        detected_amount: Optional[float],
        user_id: str = "default_user",
        contact_ids: List[str] = None
    ) -> ActionHookResult:
        """
        Execute all actions based on decision output.
        This is the main hook that connects everything.
        """
        actions_executed = []
        errors = []
        
        # 1. Execute block action for dangerous calls
        if verdict == "DANGEROUS" and risk_score >= 70:
            block_action = BlockAction(
                phone_number=caller_number,
                reason=reason,
                verdict=verdict,
                risk_score=risk_score,
                user_id=user_id
            )
            result = self.execute_block_action(block_action)
            actions_executed.append(result.details)
            if not result.success:
                errors.append(result.message)
        
        # 2. Execute report action for dangerous/suspicious calls
        if verdict in ["DANGEROUS", "SUSPICIOUS"]:
            report_action = ReportAction(
                phone_number=caller_number,
                verdict=verdict,
                tags=scam_tags,
                confidence=risk_score / 100,
                source="system",
                user_id=user_id
            )
            result = self.execute_report_action(report_action)
            actions_executed.append(result.details)
            if not result.success:
                errors.append(result.message)
        
        # 3. Execute trusted alert for high severity
        if contact_ids and (risk_score >= 70 or (detected_amount and detected_amount >= 50000)):
            alert_action = TrustedAlertAction(
                phone_number=caller_number,
                scam_category=self._get_category(scam_tags),
                reason=reason,
                amount_at_risk=detected_amount,
                contact_ids=contact_ids,
                user_id=user_id,
                severity="critical" if risk_score >= 90 else "high"
            )
            result = self.execute_trusted_alert_action(alert_action)
            actions_executed.append(result.details)
            if not result.success:
                errors.append(result.message)
        
        return ActionHookResult(
            success=len(errors) == 0,
            actions_executed=actions_executed,
            errors=errors,
            summary={
                "total_actions": len(actions_executed),
                "blocked": any("block" in str(a) for a in actions_executed),
                "reported": any("report" in str(a) for a in actions_executed),
                "alert_sent": any("alert" in str(a) for a in actions_executed)
            }
        )
    
    def _get_category(self, tags: List[str]) -> str:
        """Get scam category from tags."""
        if "bank_impersonation" in tags or "otp_request" in tags:
            return "Bank Fraud"
        elif "family_impersonation" in tags:
            return "Family Impersonation"
        elif "prize_win" in tags:
            return "Prize Scam"
        return "Suspicious Call"
    
    def get_action_history(self, limit: int = 20) -> List[Dict]:
        """Get recent action history."""
        return self.action_history[-limit:]


# Global instance
action_hooks = ActionHooks()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("HOUR 28: Action Hooks")
    print("="*50)
    
    # Test executing all actions
    result = action_hooks.execute_all_actions(
        call_id="test_001",
        caller_number="+15551234567",
        verdict="DANGEROUS",
        risk_score=95,
        reason="OTP request with urgent language",
        scam_tags=["otp_request", "bank_impersonation"],
        detected_amount=100000,
        user_id="user_001",
        contact_ids=["contact_1", "contact_2"]
    )
    
    print(f"✅ Actions executed: {result.summary}")
    print(f"✅ Success: {result.success}")
    print(f"✅ Actions count: {result.summary['total_actions']}")
    
    print("\n✅ Hour 28 Complete: Action hooks ready!")
    print("\n🎉 HOURS 24-28 COMPLETE! All action hooks connected!")
