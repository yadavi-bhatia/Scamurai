
"""Hour 28: Blocklist Endpoint - Blocked calls saved automatically."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn

from blocklist_persistence import BlocklistPersistence
from immutable_action_logger import ImmutableActionLogger

# Request/Response Models
class BlockRequest(BaseModel):
    phone_number: str
    reason: str
    verdict: str = "DANGEROUS"
    risk_score: float = 0
    user_id: str = "default_user"
    tags: List[str] = []


class UnblockRequest(BaseModel):
    phone_number: str
    reason: str = "User request"
    user_id: str = "default_user"


class BlockResponse(BaseModel):
    success: bool
    message: str
    block_id: Optional[str] = None
    timestamp: str


# Initialize
blocklist_storage = BlocklistPersistence()
action_logger = ImmutableActionLogger()

# Create FastAPI app
app = FastAPI(title="Blocklist API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/blocklist/block", response_model=BlockResponse)
async def block_number(request: BlockRequest):
    """
    Block a phone number.
    Blocked calls are saved automatically to persistent storage.
    """
    # Check if already blocked
    if blocklist_storage.is_blocked(request.phone_number, request.user_id):
        return BlockResponse(
            success=False,
            message=f"Number {request.phone_number} is already blocked",
            timestamp=datetime.now().isoformat()
        )
    
    # Add to blocklist
    result = blocklist_storage.add_block(
        phone_number=request.phone_number,
        reason=request.reason,
        verdict=request.verdict,
        risk_score=request.risk_score,
        user_id=request.user_id,
        tags=request.tags
    )
    
    # Log to immutable chain
    action_logger.log_action(
        action_type="block",
        incident_id=f"block_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        details={
            "phone_number": request.phone_number,
            "reason": request.reason,
            "verdict": request.verdict,
            "risk_score": request.risk_score,
            "user_id": request.user_id
        }
    )
    
    return BlockResponse(
        success=True,
        message=f"Number {request.phone_number} blocked successfully",
        block_id=result.get("block_id"),
        timestamp=datetime.now().isoformat()
    )


@app.post("/blocklist/unblock")
async def unblock_number(request: UnblockRequest):
    """Unblock a previously blocked number."""
    result = blocklist_storage.remove_block(
        phone_number=request.phone_number,
        user_id=request.user_id,
        reason=request.reason
    )
    
    if result:
        action_logger.log_action(
            action_type="unblock",
            incident_id=f"unblock_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            details={
                "phone_number": request.phone_number,
                "reason": request.reason,
                "user_id": request.user_id
            }
        )
        return {"success": True, "message": f"Number {request.phone_number} unblocked"}
    
    raise HTTPException(status_code=404, detail="Number not found in blocklist")


@app.get("/blocklist/{user_id}")
async def get_blocklist(user_id: str):
    """Get all blocked numbers for a user."""
    blocked = blocklist_storage.get_blocked_numbers(user_id)
    return {
        "user_id": user_id,
        "total_blocked": len(blocked),
        "blocked_numbers": blocked,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/blocklist/check/{phone_number}")
async def check_blocked(phone_number: str, user_id: str = "default_user"):
    """Check if a number is blocked."""
    is_blocked = blocklist_storage.is_blocked(phone_number, user_id)
    return {
        "phone_number": phone_number,
        "is_blocked": is_blocked,
        "user_id": user_id
    }


@app.get("/blocklist/stats")
async def get_blocklist_stats():
    """Get blocklist statistics."""
    return blocklist_storage.get_statistics()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Blocklist API on http://127.0.0.1:8008")
    print("="*50)
    print("\n📋 Endpoints:")
    print("   POST /blocklist/block - Block a number")
    print("   POST /blocklist/unblock - Unblock a number")
    print("   GET /blocklist/{user_id} - Get user's blocklist")
    print("   GET /blocklist/check/{number} - Check if blocked")
    print("   GET /blocklist/stats - Get statistics")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8008)
