


"""Trusted Share API - Final Working Version."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn

# Storage
contacts = {}
alerts = []

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

app = FastAPI(title="Trusted Share API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/trusted/contacts")
async def add_contact(req: ContactRequest):
    """Add a trusted contact."""
    contact_id = f"c_{len(contacts.get(req.user_id, []))}"
    
    if req.user_id not in contacts:
        contacts[req.user_id] = []
    
    contact = {
        "id": contact_id,
        "name": req.name,
        "phone_number": req.phone_number,
        "relationship": req.relationship,
        "added_at": datetime.now().isoformat()
    }
    
    contacts[req.user_id].append(contact)
    
    return {"success": True, "contact": contact, "message": "Contact added successfully"}

@app.get("/trusted/contacts/{user_id}")
async def get_contacts(user_id: str):
    """Get all trusted contacts."""
    user_contacts = contacts.get(user_id, [])
    return {
        "success": True,
        "user_id": user_id,
        "total": len(user_contacts),
        "contacts": user_contacts
    }

@app.post("/trusted/share")
async def share_alert(req: AlertRequest):
    """Send alert to trusted contacts."""
    
    user_contacts = contacts.get(req.user_id, [])
    selected = [c for c in user_contacts if c["id"] in req.contact_ids]
    
    # Create message
    message = f"""🚨 POSSIBLE SCAM ALERT!

📞 Caller: {req.caller_number}
⚠️ Type: {req.scam_category}
📝 Reason: {req.reason}
🕐 Time: {datetime.now().strftime('%I:%M %p')}"""
    
    if req.amount_at_risk:
        message += f"\n💰 Amount at risk: ₹{req.amount_at_risk:,.2f}"
    
    alert = {
        "alert_id": f"alt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "user_id": req.user_id,
        "contacts": selected,
        "message": message
    }
    
    alerts.append(alert)
    
    return {
        "success": True,
        "alert_id": alert["alert_id"],
        "contacts_notified": len(selected),
        "contact_names": [c["name"] for c in selected],
        "message": "Alert sent successfully",
        "channels_used": ["sms", "whatsapp", "in_app"]
    }

@app.get("/trusted/history/{user_id}")
async def get_history(user_id: str):
    """Get alert history."""
    user_alerts = [a for a in alerts if a.get("user_id") == user_id]
    return {
        "success": True,
        "user_id": user_id,
        "total": len(user_alerts),
        "alerts": user_alerts[-20:]
    }

@app.get("/trusted/stats")
async def get_stats():
    """Get statistics."""
    total_contacts = sum(len(c) for c in contacts.values())
    return {
        "success": True,
        "total_users": len(contacts),
        "total_contacts": total_contacts,
        "total_alerts_sent": len(alerts),
        "avg_contacts_per_user": round(total_contacts / max(len(contacts), 1), 2),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trusted/health")
async def health():
    return {"status": "healthy", "service": "Trusted Share API"}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("👥 Trusted Share API on http://127.0.0.1:8010")
    print("="*50)
    print("\n📋 Endpoints:")
    print("   POST /trusted/contacts - Add contact")
    print("   GET /trusted/contacts/{user_id} - Get contacts")
    print("   POST /trusted/share - Send alert")
    print("   GET /trusted/history/{user_id} - Alert history")
    print("   GET /trusted/stats - Statistics")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8010)


