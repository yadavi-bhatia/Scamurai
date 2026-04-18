
"""Hour 16: Glue API - Backend glue endpoint for final integration."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from incident_storage import IncidentStorage
from immutable_logger import ImmutableLogger
from decision_logger import DecisionLogger
from summary_card import create_summary_card, print_summary_card


class WebhookRequest(BaseModel):
    CallSid: str
    To: str
    From: str
    CallStatus: str = "in-progress"


# Initialize components
incident_storage = IncidentStorage("data/incidents.jsonl")
immutable_logger = ImmutableLogger("data/immutable_log.jsonl")
decision_logger = DecisionLogger("data/decisions.jsonl")

app = FastAPI(title="Person 4 - Complete System", version="4.0.0")


@app.post("/webhook")
async def process_webhook(request: WebhookRequest):
    """Main glue endpoint - ties everything together."""
    try:
        # Store incident
        incident = incident_storage.store_incident({
            "call_id": request.CallSid,
            "scammer": request.From,
            "victim": request.To,
            "timestamp": datetime.now().isoformat()
        })
        
        # Log to immutable chain
        immutable_entry = immutable_logger.log_entry({
            "incident_id": incident['incident_id'],
            "call_id": request.CallSid
        })
        
        # Simulate decision (integrate with your consensus engine here)
        verdict = "DANGEROUS"
        score = 95.5
        reason = "OTP request detected"
        evidence = {
            "transcript": "Share your OTP",
            "reason_codes": ["otp_request", "urgent_action"]
        }
        
        # Log decision
        decision = decision_logger.log_decision(
            call_id=request.CallSid,
            verdict=verdict,
            score=score,
            reason=reason,
            evidence=evidence,
            incident_hash=immutable_entry['hash'][:16],
            chain_position=immutable_entry['index']
        )
        
        # Create summary card
        summary = create_summary_card(
            call_id=request.CallSid,
            verdict=verdict,
            risk_score=score,
            caller_type="ai-likely",
            reason=reason,
            indicators=evidence['reason_codes'],
            transcript=evidence['transcript'],
            scam_phrases=["OTP"],
            caller_number=request.From,
            victim_number=request.To,
            incident_hash=immutable_entry['hash'][:16],
            chain_position=immutable_entry['index']
        )
        
        print_summary_card(summary)
        
        return {
            "status": "success",
            "data": {
                "action": "block",
                "risk_score": score,
                "incident_id": incident['incident_id'],
                "evidence_hash": immutable_entry['hash'][:16]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "4.0.0"}


@app.get("/stats")
async def stats():
    return {
        "incidents": len(incident_storage.get_all_incidents()),
        "decisions": decision_logger.get_statistics(),
        "log_chain": immutable_logger.verify_all()
    }


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Glue API on http://127.0.0.1:8003")
    uvicorn.run(app, host="127.0.0.1", port=8003)
