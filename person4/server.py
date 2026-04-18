
"""Minimal working server for Person 4."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

# Create FastAPI app
app = FastAPI(title="Person 4 - Scam Detection")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Person 4 Server is Running!",
        "status": "active",
        "time": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Person 4"}

@app.post("/exotel-webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
        return {
            "status": "received",
            "data": body,
            "message": "Webhook received successfully"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Person 4 Server Starting...")
    print("="*50)
    print("\n📍 Server URL: http://localhost:8000")
    print("📋 Endpoints:")
    print("   GET  / - Root endpoint")
    print("   GET  /health - Health check")
    print("   POST /exotel-webhook - Webhook receiver")
    print("\n⚠️  Press CTRL+C to stop\n")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
