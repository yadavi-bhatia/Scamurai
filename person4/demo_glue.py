
"""Hour 20: Demo Glue Layer - Final stable demo endpoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn

from incident_storage import IncidentStorage
from immutable_logger import ImmutableLogger
from decision_logger import DecisionLogger
from summary_card import create_summary_card, print_summary_card
from alert_actions import AlertAction, AlertLevel
from chain_verifier import ChainVerifier
from judge_report import JudgeReport


class DemoRequest(BaseModel):
    CallSid: str
    To: str
    From: str
    CallStatus: str = "in-progress"


# Initialize components
incident_storage = IncidentStorage("data/incidents.jsonl")
immutable_logger = ImmutableLogger("data/immutable_log.jsonl")
decision_logger = DecisionLogger("data/decisions.jsonl")
alert_actions = AlertAction("data/alerts.jsonl")
chain_verifier = ChainVerifier("data/immutable_log.jsonl")
judge_reporter = JudgeReport("data/judge_reports")

app = FastAPI(title="Scam Detection - Demo", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/demo/webhook")
async def demo_webhook(request: DemoRequest):
    """Complete demo endpoint."""
    
    print("\n" + "="*70)
    print("🎯 DEMO: Processing Call")
    print("="*70)
    print(f"📞 Call: {request.CallSid} | From: {request.From} | To: {request.To}")
    
    # Store incident
    incident = incident_storage.store_incident({
        "call_id": request.CallSid,
        "scammer": request.From,
        "victim": request.To,
        "final_risk": "DANGEROUS",
        "final_score": 95.5,
        "timestamp": datetime.now().isoformat()
    })
    
    # Log to immutable chain
    immutable_entry = immutable_logger.log_entry({
        "incident_id": incident['incident_id'],
        "call_id": request.CallSid,
        "verdict": "DANGEROUS"
    })
    
    # Send alert
    alert_actions.send_alert(
        level=AlertLevel.CRITICAL,
        title="SCAM DETECTED",
        message=f"Scam call from {request.From}",
        incident_id=incident['incident_id']
    )
    
    # Log decision
    decision_logger.log_decision(
        call_id=request.CallSid,
        verdict="DANGEROUS",
        score=95.5,
        reason="OTP request detected",
        evidence={"transcript": "Share your OTP"},
        incident_hash=immutable_entry['hash'][:16],
        chain_position=immutable_entry['index']
    )
    
    # Create summary card
    summary = create_summary_card(
        call_id=request.CallSid,
        verdict="DANGEROUS",
        risk_score=95.5,
        caller_type="ai-likely",
        reason="OTP request detected",
        indicators=["otp_request"],
        transcript="Share your OTP",
        scam_phrases=["OTP"],
        caller_number=request.From,
        victim_number=request.To,
        incident_hash=immutable_entry['hash'][:16],
        chain_position=immutable_entry['index']
    )
    
    print_summary_card(summary)
    
    # Generate judge report
    judge_reporter.save_report({
        "incident_id": incident['incident_id'],
        "call_id": request.CallSid,
        "final_risk": "DANGEROUS",
        "final_score": 95.5,
        "caller_type": "ai-likely",
        "decision_reason": "OTP request detected",
        "incident_hash": immutable_entry['hash'][:16]
    })
    
    return {
        "status": "success",
        "message": "✅ Demo complete!",
        "data": {
            "action": "block",
            "play_hold_music": True,
            "risk_score": 95.5,
            "incident_id": incident['incident_id'],
            "evidence_hash": immutable_entry['hash'][:16]
        }
    }


@app.get("/demo/status")
async def demo_status():
    chain = chain_verifier.verify_full_chain()
    return {
        "status": "ready",
        "version": "5.0.0",
        "chain_valid": chain.get('valid', False),
        "total_entries": chain.get('entries', 0)
    }


@app.get("/")
async def root():
    return {
        "message": "Scam Detection Demo - Person 4 Complete",
        "endpoints": {
            "POST /demo/webhook": "Process a call",
            "GET /demo/status": "System status"
        }
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 DEMO GLUE LAYER - FINAL STABLE VERSION")
    print("="*60)
    print("\n📍 Server: http://127.0.0.1:8005")
    print("📋 Endpoints:")
    print("   POST /demo/webhook - Process a call")
    print("   GET  /demo/status  - System status")
    print("\n🚀 Ready for demo!")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8005)
