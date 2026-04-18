
"""Complete Person 4 Server with Full Integration."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import Dict, Any

# Import Person 4 modules
from models import (
    VoiceAnalysisResult, TranscriptAnalysisResult, 
    ExotelMetadata, FinalDecision, RiskLevel, CallerType
)
from main import Person4Agent

# Create FastAPI app
app = FastAPI(
    title="Scam Detection System - Person 4",
    description="Consensus Agent with Tamper-Evident Logging",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Person 4 Agent
agent = Person4Agent()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Scam Detection System - Person 4",
        "description": "Consensus Agent with Tamper-Evident Logging",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "POST /exotel-webhook": "Receive Exotel calls",
            "GET /health": "Health check",
            "GET /stats": "System statistics"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        is_valid, errors = agent.verify_log_integrity()
        return {
            "status": "healthy",
            "module": "Person 4 - Consensus Agent",
            "version": "2.0.0",
            "log_verified": is_valid,
            "port": 8001
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    try:
        history = agent.get_call_history(100)
        risk_counts = {}
        for record in history:
            risk = record.get('final_risk', 'UNKNOWN')
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        return {
            "total_calls_processed": len(history),
            "risk_distribution": risk_counts,
            "recent_calls": history[-5:] if history else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/exotel-webhook")
async def exotel_webhook(request: Request):
    """
    Webhook endpoint for Exotel to send call data.
    """
    try:
        # Parse incoming request
        payload = await request.json()
        
        print(f"\n📞 Received webhook from Exotel:")
        print(f"   CallSid: {payload.get('CallSid', 'unknown')}")
        print(f"   From: {payload.get('From', 'unknown')}")
        print(f"   To: {payload.get('To', 'unknown')}")
        
        # Create Exotel metadata
        exotel_meta = ExotelMetadata(
            call_id=payload.get('CallSid', 'unknown'),
            stream_id=payload.get('StreamSid', 'unknown'),
            timestamp=datetime.now(),
            routing_path=f"exotel→{payload.get('To', 'unknown')}",
            victim_number=payload.get('To', ''),
            scammer_number=payload.get('From', ''),
            transfer_status=payload.get('CallStatus', 'connected'),
            call_duration=None
        )
        
        # Create voice analysis (will be replaced by Person 2)
        voice_result = VoiceAnalysisResult(
            caller_type=CallerType.AI,
            voice_score=85.0,
            signal_quality=0.8,
            confidence=0.9,
            raw_features=None
        )
        
        # Create transcript analysis (will be replaced by Person 3)
        transcript_result = TranscriptAnalysisResult(
            scam_likelihood=95.0,
            reason_codes=["otp_request", "urgent_action"],
            scam_phrases_found=["OTP", "account blocked"],
            transcript_text="Share your OTP to secure your account",
            confidence=0.95
        )
        
        # Process through Person 4
        decision = agent.process_call(voice_result, transcript_result, exotel_meta)
        
        # Return response
        if decision.final_risk == RiskLevel.DANGEROUS:
            response = {
                "action": "block",
                "message": "Call blocked - scam detected",
                "play_hold_music": True,
                "risk_score": decision.final_score,
                "caller_type": decision.caller_type.value,
                "reason_codes": decision.reason_codes[:3],
                "incident_hash": decision.incident_hash[:16]
            }
        elif decision.final_risk == RiskLevel.SUSPICIOUS:
            response = {
                "action": "warn",
                "message": "Suspicious call - proceed with caution",
                "play_hold_music": False,
                "risk_score": decision.final_score,
                "caller_type": decision.caller_type.value,
                "reason_codes": decision.reason_codes[:3],
                "incident_hash": decision.incident_hash[:16]
            }
        else:
            response = {
                "action": "allow",
                "message": "Call appears safe",
                "play_hold_music": False,
                "risk_score": decision.final_score,
                "caller_type": decision.caller_type.value,
                "reason_codes": [],
                "incident_hash": decision.incident_hash[:16]
            }
        
        return {
            "status": "success",
            "data": response
        }
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 PERSON 4 - COMPLETE SERVER")
    print("="*60)
    print("\n📡 Server Configuration:")
    print("   Host: 127.0.0.1")
    print("   Port: 8001")
    print("\n📋 Available Endpoints:")
    print("   POST /exotel-webhook - Receive Exotel calls")
    print("   GET  /health - Health check")
    print("   GET  /stats - System statistics")
    print("   GET  / - API information")
    print("\n🌐 Server URL: http://localhost:8001")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
