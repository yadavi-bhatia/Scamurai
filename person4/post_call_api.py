
"""Post-Call Risk Action API."""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn

from risk_actions import RiskActionEngine
from reputation_manager import ReputationManager
from trusted_contacts import TrustedContactsManager
from blocklist_manager import BlocklistManager


class FinalizeRequest(BaseModel):
    call_id: str
    caller_number: str
    verdict: str
    risk_score: float
    scam_tags: List[str]
    transcript_summary: str
    detected_amount: Optional[float] = None
    family_impersonation_flag: bool = False
    deepfake_flag: bool = False
    user_id: str = "default_user"


class BlockRequest(BaseModel):
    user_id: str
    phone_number: str
    reason: str


class ReportRequest(BaseModel):
    user_id: str
    phone_number: str
    verdict: str
    tags: List[str]
    confidence: float


class ContactRequest(BaseModel):
    user_id: str
    name: str
    phone_number: str
    relationship: str = "friend"


class AlertRequest(BaseModel):
    user_id: str
    contact_ids: List[str]
    caller_number: str
    scam_category: str
    reason: str
    amount_at_risk: Optional[float] = None


# Initialize
risk_engine = RiskActionEngine()
reputation = ReputationManager()
trusted = TrustedContactsManager()
blocklist = BlocklistManager()

app = FastAPI(title="Risk Action API", version="1.0")


@app.post("/calls/{call_id}/finalize")
async def finalize_call(call_id: str, req: FinalizeRequest):
    decision = risk_engine.decide(
        call_id=call_id,
        caller_number=req.caller_number,
        verdict=req.verdict,
        risk_score=req.risk_score,
        scam_tags=req.scam_tags,
        transcript_summary=req.transcript_summary,
        detected_amount=req.detected_amount,
        family_impersonation_flag=req.family_impersonation_flag,
        deepfake_flag=req.deepfake_flag
    )
    
    if decision.blocklist_updated:
        blocklist.block_number(req.user_id, req.caller_number, decision.explanation, req.verdict, req.risk_score)
    
    if decision.shared_list_updated:
        reputation.add_report(req.caller_number, req.verdict, req.scam_tags, req.risk_score / 100)
    
    return {
        "call_id": call_id,
        "action_taken": decision.action_taken,
        "blocklist_updated": decision.blocklist_updated,
        "shared_list_updated": decision.shared_list_updated,
        "trusted_contact_prompt_shown": decision.trusted_contact_prompt_shown,
        "severity": decision.severity,
        "explanation": decision.explanation,
        "next_steps": decision.next_steps
    }


@app.post("/numbers/block")
async def block_number(req: BlockRequest):
    return blocklist.block_number(req.user_id, req.phone_number, req.reason)


@app.post("/numbers/report")
async def report_number(req: ReportRequest):
    return reputation.add_report(req.phone_number, req.verdict, req.tags, req.confidence, "user", req.user_id)


@app.get("/numbers/{phone_number}/reputation")
async def get_reputation(phone_number: str):
    return reputation.get_reputation(phone_number)


@app.post("/trusted-contacts")
async def add_contact(req: ContactRequest):
    return trusted.add_contact(req.user_id, req.name, req.phone_number, req.relationship)


@app.get("/users/{user_id}/contacts")
async def get_contacts(user_id: str):
    return {"contacts": trusted.get_contacts(user_id)}


@app.post("/alerts/send")
async def send_alert(req: AlertRequest):
    alert_data = {
        "caller_number": req.caller_number,
        "scam_category": req.scam_category,
        "reason": req.reason,
        "amount_at_risk": req.amount_at_risk
    }
    return trusted.send_alert(req.user_id, req.contact_ids, alert_data)


@app.get("/statistics")
async def get_statistics():
    return {
        "risk_engine": risk_engine.get_stats(),
        "reputation": reputation.get_statistics(),
        "trusted_contacts": trusted.get_statistics(),
        "blocklist": blocklist.get_statistics(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "module": "Risk Action API"}


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Risk Action API on http://127.0.0.1:8006")
    print("="*50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8006)
