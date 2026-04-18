
"""Hour 36: Final Demo Glue - Stable final presentation support."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uvicorn

from incident_summary_card import create_demo_summary, print_summary_card

# Request model
class DemoCallRequest(BaseModel):
    call_id: str
    caller_number: str
    victim_number: str
    verdict: str = "DANGEROUS"
    risk_score: float = 98.5

# Create FastAPI app
app = FastAPI(
    title="Scam Detection System - FINAL DEMO",
    description="Complete scam detection with blocklist, reputation, and trusted alerts",
    version="5.0.0 - FINAL"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with demo information."""
    return {
        "message": "Scam Detection System - FINAL DEMO",
        "version": "5.0.0",
        "status": "READY FOR PRESENTATION",
        "demo_instructions": {
            "step_1": "Start all servers (blocklist, reputation, trusted_share)",
            "step_2": "POST to /demo/call with call details",
            "step_3": "View summary card and actions taken"
        },
        "endpoints": {
            "POST /demo/call": "Process a demo scam call",
            "GET /demo/summary/{incident_id}": "Get incident summary",
            "GET /demo/status": "System status",
            "GET /demo/dashboard": "HTML Dashboard"
        }
    }


@app.post("/demo/call")
async def demo_call(request: DemoCallRequest):
    """
    Process a demo scam call and return complete response.
    This simulates the full scam detection flow.
    """
    
    print("\n" + "="*70)
    print("🎯 DEMO CALL RECEIVED")
    print("="*70)
    print(f"📞 Call ID: {request.call_id}")
    print(f"📞 From: {request.caller_number}")
    print(f"📞 To: {request.victim_number}")
    print(f"🎯 Verdict: {request.verdict}")
    print(f"📊 Risk Score: {request.risk_score}")
    
    # Create incident summary
    incident_id = f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Determine actions based on verdict
    should_block = request.verdict == "DANGEROUS"
    should_report = request.verdict in ["DANGEROUS", "SUSPICIOUS"]
    should_alert = request.verdict == "DANGEROUS" and request.risk_score >= 70
    
    # Create summary card
    summary = create_demo_summary(
        incident_id=incident_id,
        call_id=request.call_id,
        verdict=request.verdict,
        risk_score=int(request.risk_score),
        caller_number=request.caller_number,
        blocked=should_block,
        reported=should_report,
        alert_sent=should_alert,
        contacts=["Mom", "Dad"] if should_alert else []
    )
    
    # Print for demo
    print_summary_card(summary)
    
    # Return response
    return {
        "status": "success",
        "message": "✅ Demo call processed successfully",
        "incident_id": incident_id,
        "verdict": request.verdict,
        "risk_score": request.risk_score,
        "actions_taken": {
            "blocked": should_block,
            "reported_to_community": should_report,
            "trusted_alert_sent": should_alert
        },
        "summary": summary.dict(),
        "next_steps": [
            "Number added to blocklist" if should_block else None,
            "Reported to community spam list" if should_report else None,
            "Alert sent to trusted contacts" if should_alert else None
        ]
    }


@app.get("/demo/summary/{incident_id}")
async def get_summary(incident_id: str):
    """Get incident summary by ID."""
    summary = create_demo_summary(incident_id=incident_id)
    return summary.dict()


@app.get("/demo/status")
async def demo_status():
    """Get demo system status."""
    return {
        "status": "ready",
        "version": "5.0.0 - FINAL",
        "services": {
            "scam_detection": "active",
            "blocklist": "active (port 8008)",
            "reputation": "active (port 8009)",
            "trusted_contacts": "active (port 8010)"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/demo/dashboard", response_class=HTMLResponse)
async def demo_dashboard():
    """HTML Dashboard for demo presentation."""
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scam Detection Demo - Final Presentation</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
            }
            .header {
                background: white;
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header h1 {
                color: #333;
                margin: 0;
                font-size: 2.5em;
            }
            .header p {
                color: #666;
                margin: 10px 0 0;
            }
            .card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .card h2 {
                color: #667eea;
                margin-top: 0;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            .status-success {
                background: #27ae60;
                color: white;
            }
            .endpoint {
                background: #f5f5f5;
                padding: 10px;
                border-radius: 8px;
                font-family: monospace;
                margin: 10px 0;
            }
            .button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
            }
            .button:hover {
                background: #5a67d8;
            }
            .footer {
                text-align: center;
                color: white;
                padding: 20px;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Scam Detection System</h1>
                <p>Complete Solution with Blocklist, Reputation & Trusted Alerts</p>
                <p><span class="status-badge status-success">DEMO READY</span></p>
            </div>
            
            <div class="card">
                <h2>📊 System Status</h2>
                <p><strong>Status:</strong> ✅ All systems operational</p>
                <p><strong>Version:</strong> 5.0.0 - FINAL</p>
                <p><strong>Ready for:</strong> Final Presentation</p>
            </div>
            
            <div class="card">
                <h2>🔧 Services Running</h2>
                <ul>
                    <li>✅ Scam Detection Engine - Active</li>
                    <li>✅ Blocklist API (Port 8008) - Active</li>
                    <li>✅ Reputation API (Port 8009) - Active</li>
                    <li>✅ Trusted Share API (Port 8010) - Active</li>
                    <li>✅ Tamper-Evident Logging - Active</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>📋 Test Endpoints</h2>
                <div class="endpoint">POST /demo/call - Process a scam call</div>
                <div class="endpoint">GET /demo/status - System status</div>
                <div class="endpoint">GET /demo/summary/{id} - Get incident summary</div>
            </div>
            
            <div class="card">
                <h2>🚀 Quick Test</h2>
                <button class="button" onclick="testCall()">Test Scam Call</button>
                <div id="result" style="margin-top: 15px; padding: 10px; background: #f5f5f5; border-radius: 8px; display: none;"></div>
            </div>
        </div>
        
        <div class="footer">
            <p>🔒 All evidence is tamper-evident with SHA-256 hash chaining</p>
            <p>© 2026 Scam Detection System - Person 4 Complete</p>
        </div>
        
        <script>
            async function testCall() {
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = 'Processing...';
                
                try {
                    const response = await fetch('/demo/call', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            call_id: 'DEMO_' + Date.now(),
                            caller_number: '+15551234567',
                            victim_number: '+919876543210',
                            verdict: 'DANGEROUS',
                            risk_score: 98.5
                        })
                    });
                    const data = await response.json();
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (error) {
                    resultDiv.innerHTML = 'Error: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 FINAL DEMO GLUE - READY FOR PRESENTATION")
    print("="*70)
    print("\n📍 Demo Server: http://127.0.0.1:8050")
    print("📋 Available Endpoints:")
    print("   POST /demo/call - Process a scam call")
    print("   GET  /demo/status - System status")
    print("   GET  /demo/summary/{id} - Incident summary")
    print("   GET  /demo/dashboard - HTML Dashboard")
    print("\n🌐 Open Dashboard: http://127.0.0.1:8050/demo/dashboard")
    print("\n🚀 Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8050)
