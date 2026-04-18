
"""Hour 24: Final Demo - Stable final presentation support."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import uvicorn
import json
from pathlib import Path

# Import all components
from incident_storage import IncidentStorage
from immutable_logger import ImmutableLogger
from decision_logger import DecisionLogger
from summary_card import create_summary_card, print_summary_card
from alert_actions import AlertAction, AlertLevel
from chain_verifier import ChainVerifier
from judge_report import JudgeReport
from forensic_record import ForensicRecordBuilder
from integrity_test import IntegrityTest
from summary_validator import SummaryValidator


class DemoRequest(BaseModel):
    CallSid: str
    To: str
    From: str
    CallStatus: str = "in-progress"


# Initialize all components
incident_storage = IncidentStorage("data/incidents.jsonl")
immutable_logger = ImmutableLogger("data/immutable_log.jsonl")
decision_logger = DecisionLogger("data/decisions.jsonl")
alert_actions = AlertAction("data/alerts.jsonl")
chain_verifier = ChainVerifier("data/immutable_log.jsonl")
judge_reporter = JudgeReport("data/judge_reports")
forensic_builder = ForensicRecordBuilder()
integrity_tester = IntegrityTest("data/immutable_log.jsonl")
summary_validator = SummaryValidator()

# Create FastAPI app
app = FastAPI(
    title="Scam Detection System - FINAL DEMO",
    description="Complete scam detection with tamper-evident logging",
    version="6.0.0 - FINAL"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/demo/webhook")
async def demo_webhook(request: DemoRequest):
    """FINAL DEMO ENDPOINT - Complete presentation flow."""
    
    print("\n" + "="*70)
    print("🎯 FINAL DEMO - SCAM DETECTION SYSTEM")
    print("="*70)
    print(f"📞 Call ID: {request.CallSid}")
    print(f"📞 From: {request.From}")
    print(f"📞 To: {request.To}")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Store incident
    incident = incident_storage.store_incident({
        "call_id": request.CallSid,
        "scammer_number": request.From,
        "victim_number": request.To,
        "timestamp": datetime.now().isoformat(),
        "final_risk": "DANGEROUS",
        "final_score": 98.5,
        "caller_type": "ai-likely",
        "decision_reason": "OTP request detected with urgent language",
        "reason_codes": ["otp_request", "urgent_action", "bank_impersonation"],
        "transcript_excerpt": "Your account is compromised. Share the OTP sent to your phone immediately.",
        "scam_phrases": ["OTP", "compromised", "immediately"],
        "confidence": 0.95
    })
    print(f"\n✅ Step 1: Incident stored - {incident['incident_id']}")
    
    # Step 2: Log to immutable chain
    immutable_entry = immutable_logger.log_entry({
        "incident_id": incident['incident_id'],
        "call_id": request.CallSid,
        "verdict": "DANGEROUS",
        "score": 98.5
    })
    print(f"✅ Step 2: Immutable entry #{immutable_entry['index']} - Hash: {immutable_entry['hash'][:16]}...")
    
    # Step 3: Send critical alert
    alert = alert_actions.send_alert(
        level=AlertLevel.CRITICAL,
        title="SCAM DETECTED",
        message=f"High-risk scam call from {request.From}",
        incident_id=incident['incident_id'],
        call_id=request.CallSid
    )
    print(f"✅ Step 3: Alert sent - {alert['alert_id']}")
    
    # Step 4: Log decision
    decision = decision_logger.log_decision(
        call_id=request.CallSid,
        verdict="DANGEROUS",
        score=98.5,
        reason="OTP request detected with urgent language",
        evidence={
            "transcript": "Share your OTP",
            "reason_codes": ["otp_request", "urgent_action"],
            "caller_type": "ai-likely"
        },
        incident_hash=immutable_entry['hash'][:16],
        chain_position=immutable_entry['index']
    )
    print(f"✅ Step 4: Decision logged - {decision['decision_id']}")
    
    # Step 5: Create summary card
    summary = create_summary_card(
        call_id=request.CallSid,
        verdict="DANGEROUS",
        risk_score=98.5,
        caller_type="ai-likely",
        reason="OTP request detected with urgent language",
        indicators=["otp_request", "urgent_action", "bank_impersonation"],
        transcript="Your account is compromised. Share the OTP sent to your phone immediately.",
        scam_phrases=["OTP", "compromised", "immediately"],
        caller_number=request.From,
        victim_number=request.To,
        incident_hash=immutable_entry['hash'][:16],
        chain_position=immutable_entry['index'],
        duration_seconds=47
    )
    print_summary_card(summary)
    print(f"✅ Step 5: Summary card generated")
    
    # Step 6: Generate forensic record
    forensic_data = {
        "call_id": request.CallSid,
        "scammer_number": request.From,
        "victim_number": request.To,
        "final_risk": "DANGEROUS",
        "final_score": 98.5,
        "confidence": 0.95,
        "caller_type": "ai-likely",
        "decision_reason": "OTP request detected with urgent language",
        "reason_codes": ["otp_request", "urgent_action"],
        "transcript_excerpt": "Share your OTP",
        "scam_phrases": ["OTP"],
        "incident_hash": immutable_entry['hash'][:16],
        "prev_hash": immutable_entry['prev_hash'][:16],
        "chain_position": immutable_entry['index']
    }
    forensic_record = forensic_builder.build_from_incident(forensic_data)
    print(f"✅ Step 6: Forensic record created - {forensic_record.record_id}")
    
    # Step 7: Generate judge report
    judge_report_data = {
        "incident_id": incident['incident_id'],
        "call_id": request.CallSid,
        "final_risk": "DANGEROUS",
        "final_score": 98.5,
        "caller_type": "ai-likely",
        "decision_reason": "OTP request detected",
        "incident_hash": immutable_entry['hash'][:16],
        "scammer_number": request.From,
        "victim_number": request.To,
        "timestamp": datetime.now().isoformat()
    }
    report_path = judge_reporter.save_report(judge_report_data)
    print(f"✅ Step 7: Judge report saved - {report_path}")
    
    # Step 8: Return final response
    return {
        "status": "success",
        "message": "✅ FINAL DEMO - Scam Detection Complete",
        "data": {
            "action": "block",
            "play_hold_music": True,
            "risk_score": 98.5,
            "caller_type": "ai-likely",
            "incident_id": incident['incident_id'],
            "evidence_hash": immutable_entry['hash'][:16],
            "chain_position": immutable_entry['index'],
            "forensic_record_id": forensic_record.record_id
        }
    }


@app.get("/demo/status")
async def demo_status():
    """Get demo system status."""
    chain = chain_verifier.verify_full_chain()
    incidents = incident_storage.get_all_incidents()
    
    return {
        "status": "ready",
        "version": "6.0.0 - FINAL",
        "chain_valid": chain.get('valid', False),
        "total_entries": chain.get('entries', 0),
        "total_incidents": len(incidents),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/demo/integrity")
async def demo_integrity():
    """Run integrity test."""
    result = integrity_tester.run_full_test()
    return result


@app.get("/demo/forensic/{incident_id}")
async def get_forensic_record(incident_id: str):
    """Get forensic record by incident ID."""
    # Search for the record
    records_path = Path("data/forensic_records.jsonl")
    if not records_path.exists():
        raise HTTPException(status_code=404, detail="No forensic records found")
    
    with open(records_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if data.get('record_id') == incident_id or data.get('call_id') == incident_id:
                    return {"status": "success", "record": data}
    
    raise HTTPException(status_code=404, detail=f"Record {incident_id} not found")


@app.get("/demo/chain")
async def get_chain():
    """Get the full chain summary."""
    return chain_verifier.get_chain_summary()


@app.get("/")
async def root():
    """Root endpoint with demo information."""
    return {
        "message": "Scam Detection System - FINAL DEMO",
        "version": "6.0.0",
        "status": "READY FOR PRESENTATION",
        "endpoints": {
            "POST /demo/webhook": "Process a scam call",
            "GET /demo/status": "System status",
            "GET /demo/integrity": "Run integrity test",
            "GET /demo/chain": "View chain summary",
            "GET /demo/forensic/{id}": "Get forensic record"
        },
        "quick_start": {
            "command": "curl -X POST http://127.0.0.1:8005/demo/webhook -H 'Content-Type: application/json' -d '{\"CallSid\":\"test\",\"To\":\"+91\",\"From\":\"+1\"}'"
        }
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 FINAL DEMO - READY FOR PRESENTATION")
    print("="*70)
    print("\n📍 Server: http://127.0.0.1:8005")
    print("📋 Available Endpoints:")
    print("   POST /demo/webhook     - Process a scam call")
    print("   GET  /demo/status      - System status")
    print("   GET  /demo/integrity   - Verify chain integrity")
    print("   GET  /demo/chain       - View chain summary")
    print("   GET  /demo/forensic/id - Get forensic record")
    print("   GET  /                 - API information")
    print("\n🚀 Press Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8005)
