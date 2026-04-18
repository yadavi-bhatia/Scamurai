"""Integration bridge between Person 1 (Exotel) and Person 4."""

from datetime import datetime
from typing import Dict, Any
from models import (
    VoiceAnalysisResult, TranscriptAnalysisResult, 
    ExotelMetadata, FinalDecision, RiskLevel, CallerType
)
from main import Person4Agent


class ExotelIntegrationBridge:
    """Bridge to receive data from Exotel webhook."""
    
    def __init__(self):
        self.agent = Person4Agent()
    
    def handle_incoming_call(self, exotel_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming call from Exotel webhook.
        
        Args:
            exotel_payload: JSON payload from Exotel webhook
            
        Returns:
            Response dict with action to take
        """
        
        # Extract Exotel metadata from payload
        exotel_meta = ExotelMetadata(
            call_id=exotel_payload.get('CallSid', 'unknown'),
            stream_id=exotel_payload.get('StreamSid', 'unknown'),
            timestamp=datetime.now(),
            routing_path=f"exotel→{exotel_payload.get('To', 'unknown')}",
            victim_number=exotel_payload.get('To', ''),
            scammer_number=exotel_payload.get('From', ''),
            transfer_status=exotel_payload.get('CallStatus', 'connected'),
            call_duration=float(exotel_payload.get('CallDuration', 0)) if exotel_payload.get('CallDuration') else None
        )
        
        # Get voice and transcript analysis
        # TODO: Replace with actual Person 2 and Person 3 integration
        voice_result = self._get_voice_analysis(exotel_payload)
        transcript_result = self._get_transcript_analysis(exotel_payload)
        
        # Process through Person 4 consensus agent
        decision = self.agent.process_call(
            voice_result, 
            transcript_result, 
            exotel_meta
        )
        
        # Return response for Exotel
        return self._get_exotel_response(decision)
    
    def _get_voice_analysis(self, payload: Dict) -> VoiceAnalysisResult:
        """
        Get voice analysis from Person 2.
        
        TODO: Replace this placeholder with actual Person 2 integration.
        Person 2 should provide real-time voice analysis.
        """
        return VoiceAnalysisResult(
            caller_type=CallerType.AI,
            voice_score=85.0,
            signal_quality=0.8,
            confidence=0.9,
            raw_features={"source": "placeholder", "note": "Replace with Person 2"}
        )
    
    def _get_transcript_analysis(self, payload: Dict) -> TranscriptAnalysisResult:
        """
        Get transcript analysis from Person 3.
        
        TODO: Replace this placeholder with actual Person 3 integration.
        Person 3 should provide real-time transcript analysis.
        """
        # Check if transcript is provided in payload
        transcript_text = payload.get('Transcript', 'Share your OTP to secure your account')
        
        return TranscriptAnalysisResult(
            scam_likelihood=95.0,
            reason_codes=["otp_request", "urgent_action", "bank_impersonation"],
            scam_phrases_found=["OTP", "account blocked", "verify immediately"],
            transcript_text=transcript_text,
            confidence=0.95
        )
    
    def _get_exotel_response(self, decision: FinalDecision) -> Dict[str, Any]:
        """
        Generate response for Exotel based on decision.
        
        Args:
            decision: Final decision from consensus agent
            
        Returns:
            Response dict for Exotel webhook
        """
        
        if decision.final_risk == RiskLevel.DANGEROUS:
            return {
                "action": "block",
                "message": "Call blocked - scam detected",
                "play_hold_music": True,
                "redirect": None,
                "risk_score": decision.final_score,
                "reason_codes": decision.reason_codes[:3],
                "caller_type": decision.caller_type.value,
                "confidence": decision.confidence
            }
        elif decision.final_risk == RiskLevel.SUSPICIOUS:
            return {
                "action": "warn",
                "message": "Suspicious call - proceed with caution",
                "play_hold_music": False,
                "redirect": None,
                "risk_score": decision.final_score,
                "reason_codes": decision.reason_codes[:3],
                "caller_type": decision.caller_type.value,
                "confidence": decision.confidence
            }
        else:  # SAFE
            return {
                "action": "allow",
                "message": "Call appears safe",
                "play_hold_music": False,
                "redirect": None,
                "risk_score": decision.final_score,
                "reason_codes": [],
                "caller_type": decision.caller_type.value,
                "confidence": decision.confidence
            }


# FastAPI endpoints
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Scam Detection System - Person 4",
    description="Consensus Agent with Tamper-Evident Logging for Scam Call Detection",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize bridge
bridge = ExotelIntegrationBridge()


@app.post("/exotel-webhook")
async def exotel_webhook(request: Request):
    """
    Webhook endpoint for Exotel to send call data.
    
    Expected payload format:
    {
        "CallSid": "CA123456789",
        "StreamSid": "ST123456789",
        "To": "+919876543210",
        "From": "+15551234567",
        "CallStatus": "in-progress",
        "CallDuration": "0"
    }
    """
    try:
        payload = await request.json()
        result = bridge.handle_incoming_call(payload)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing call: {str(e)}")


@app.post("/webhook/exotel")
async def exotel_webhook_alt(request: Request):
    """Alternative webhook endpoint for Exotel."""
    try:
        payload = await request.json()
        result = bridge.handle_incoming_call(payload)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        is_valid, errors = bridge.agent.verify_log_integrity()
        return {
            "status": "healthy",
            "module": "Person 4 - Consensus Agent",
            "version": "2.0.0",
            "log_verified": is_valid,
            "log_errors": errors if not is_valid else None
        }
    except Exception as e:
        return {
            "status": "degraded",
            "module": "Person 4",
            "error": str(e)
        }


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    try:
        history = bridge.agent.get_call_history(100)
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Scam Detection System - Person 4",
        "description": "Consensus Agent with Tamper-Evident Logging",
        "version": "2.0.0",
        "endpoints": {
            "POST /exotel-webhook": "Receive Exotel calls",
            "POST /webhook/exotel": "Alternative webhook endpoint",
            "GET /health": "Health check",
            "GET /stats": "System statistics",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "API documentation (ReDoc)"
        },
        "example_webhook_payload": {
            "CallSid": "CA123456789",
            "StreamSid": "ST123456789",
            "To": "+919876543210",
            "From": "+15551234567",
            "CallStatus": "in-progress"
        }
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 PERSON 4 - FASTAPI SERVER")
    print("="*70)
    print("\n📡 Server Configuration:")
    print("   Host: 0.0.0.0")
    print("   Port: 8000")
    print("   Reload: Enabled")
    print("\n📋 Available Endpoints:")
    print("   POST /exotel-webhook - Receive Exotel calls")
    print("   POST /webhook/exotel - Alternative webhook")
    print("   GET  /health - Health check")
    print("   GET  /stats - System statistics")
    print("   GET  /docs - Interactive API docs (Swagger UI)")
    print("   GET  /redoc - API documentation (ReDoc)")
    print("   GET  / - API information")
    print("\n🌐 Server URL: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )