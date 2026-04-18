
"""Hour 19: Backend Logging API - Query logs and search incidents."""

from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import json

from chain_verifier import ChainVerifier
from judge_report import JudgeReport
from alert_actions import AlertAction

app = FastAPI(title="Logging API", version="4.0.0")

chain_verifier = ChainVerifier("data/immutable_log.jsonl")
judge_reporter = JudgeReport()
alert_actions = AlertAction()


@app.get("/verify")
async def verify_chain():
    return chain_verifier.verify_full_chain()


@app.get("/integrity-report")
async def integrity_report():
    return {"report": chain_verifier.generate_integrity_report()}


@app.get("/incidents")
async def get_incidents(limit: int = Query(50, description="Max results")):
    incidents = []
    path = Path("data/incidents.jsonl")
    
    if path.exists():
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    incidents.append(json.loads(line))
    
    return {"total": len(incidents), "incidents": incidents[-limit:]}


@app.get("/alerts")
async def get_alerts(limit: int = Query(50, description="Max results")):
    alerts = alert_actions.get_alerts(limit)
    return {"total": len(alerts), "alerts": alerts}


@app.post("/report/{incident_id}")
async def generate_report(incident_id: str):
    # Find incident
    path = Path("data/incidents.jsonl")
    if not path.exists():
        raise HTTPException(404, "No incidents found")
    
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                inc = json.loads(line)
                if inc.get('incident_id') == incident_id:
                    report_path = judge_reporter.save_report(inc.get('data', {}))
                    return {"report_path": str(report_path)}
    
    raise HTTPException(404, f"Incident {incident_id} not found")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Logging API on http://127.0.0.1:8004")
    uvicorn.run(app, host="127.0.0.1", port=8004)
