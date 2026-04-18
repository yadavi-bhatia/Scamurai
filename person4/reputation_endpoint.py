
"""Hour 29: Reputation Endpoint - Publish flagged numbers to global list."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn

from reputation_writer import ReputationWriter
from immutable_action_logger import ImmutableActionLogger

# Request/Response Models
class ReportRequest(BaseModel):
    phone_number: str
    verdict: str
    tags: List[str]
    confidence: float
    source: str = "user"
    user_id: Optional[str] = None


class ReputationResponse(BaseModel):
    phone_number: str
    reputation_score: float
    total_reports: int
    risk_level: str


# Initialize
reputation_writer = ReputationWriter()
action_logger = ImmutableActionLogger()

app = FastAPI(title="Reputation API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/reputation/report")
async def report_number(request: ReportRequest):
    """
    Report a number to the global spam list.
    Flagged numbers are published to the community reputation list.
    """
    result = reputation_writer.add_to_community_list(
        phone_number=request.phone_number,
        verdict=request.verdict,
        tags=request.tags,
        confidence=request.confidence,
        source=request.source,
        user_id=request.user_id
    )
    
    # Log to immutable chain
    action_logger.log_action(
        action_type="report",
        incident_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        details={
            "phone_number": request.phone_number,
            "verdict": request.verdict,
            "tags": request.tags,
            "confidence": request.confidence,
            "user_id": request.user_id
        }
    )
    
    return {
        "success": True,
        "message": f"Number {request.phone_number} reported to community list",
        "reputation_score": result["reputation_score"],
        "total_reports": result["total_reports"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/reputation/{phone_number}")
async def get_reputation(phone_number: str) -> ReputationResponse:
    """Get reputation for a phone number."""
    rep = reputation_writer.get_reputation(phone_number)
    
    return ReputationResponse(
        phone_number=rep["phone_number"],
        reputation_score=rep["reputation_score"],
        total_reports=rep.get("total_reports", 0),
        risk_level=rep.get("risk_level", "unknown")
    )


@app.get("/reputation/stats")
async def get_reputation_stats():
    """Get community reputation statistics."""
    return reputation_writer.get_community_statistics()


@app.get("/reputation/top/{limit}")
async def get_top_reported(limit: int = 10):
    """Get top reported numbers."""
    top = reputation_writer.get_top_reported(limit)
    return {
        "limit": limit,
        "top_spammers": top,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/reputation/bulk-report")
async def bulk_report(reports: List[ReportRequest]):
    """Report multiple numbers at once."""
    results = []
    for report in reports:
        result = reputation_writer.add_to_community_list(
            phone_number=report.phone_number,
            verdict=report.verdict,
            tags=report.tags,
            confidence=report.confidence,
            source=report.source,
            user_id=report.user_id
        )
        results.append(result)
    
    action_logger.log_action(
        action_type="bulk_report",
        incident_id=f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        details={"count": len(reports), "numbers": [r.phone_number for r in reports]}
    )
    
    return {
        "success": True,
        "reported_count": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🌍 Reputation API on http://127.0.0.1:8009")
    print("="*50)
    print("\n📋 Endpoints:")
    print("   POST /reputation/report - Report a number")
    print("   GET /reputation/{number} - Get reputation")
    print("   GET /reputation/stats - Get statistics")
    print("   GET /reputation/top/{limit} - Top spammers")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8009)
