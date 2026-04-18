


"""Hour 23: Documentation - Backend and logging assumptions."""

from datetime import datetime
from pathlib import Path


class DocumentationGenerator:
    """Generate documentation for backend and logging assumptions."""
    
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_assumptions_doc(self) -> str:
        """Generate assumptions documentation."""
        
        current_time = datetime.now().isoformat()
        
        doc = f"""
================================================================================
                    PERSON 4 - SYSTEM ASSUMPTIONS
================================================================================
Generated: {current_time}
Version: 1.0.0

================================================================================
1. BACKEND ASSUMPTIONS
================================================================================

1.1 Exotel Integration
    - Exotel webhook sends POST requests with CallSid, To, From fields
    - Webhook endpoint expects JSON payload
    - Response format is JSON with action and message

1.2 Voice Analysis (Person 2)
    - Voice analysis provides caller_type (ai-likely/human-likely/uncertain)
    - Voice score ranges 0-100
    - Signal quality ranges 0-1
    - Confidence ranges 0-1

1.3 Transcript Analysis (Person 3)
    - Transcript provides scam_likelihood 0-100
    - Reason codes indicate specific scam types
    - Scam phrases list detected keywords

1.4 Consensus Engine
    - Weighted combination: Transcript 50%, Voice 30%, Behavioral 20%
    - Thresholds: DANGEROUS >=70, SUSPICIOUS >=40, SAFE <40
    - Poor audio quality increases transcript weight

================================================================================
2. LOGGING ASSUMPTIONS
================================================================================

2.1 Tamper-Evident Log
    - SHA-256 hashing for each entry
    - Chain links using prev_hash
    - Genesis block hash = SHA-256("GENESIS")
    - Append-only - never modify existing entries

2.2 Hash Chain Structure
    - index: integer position
    - timestamp: ISO format datetime
    - prev_hash: 64-character hex string
    - data: incident information
    - hash: 64-character hex string

2.3 Verification
    - Any modification breaks hash
    - Chain broken if prev_hash doesn't match
    - Full verification recomputes all hashes

================================================================================
3. STORAGE ASSUMPTIONS
================================================================================

3.1 File Locations
    - Incidents: data/incidents.jsonl
    - Immutable log: data/immutable_log.jsonl
    - Decisions: data/decisions.jsonl
    - Alerts: data/alerts.jsonl
    - Reports: data/judge_reports/
    - Forensic records: data/forensic_records.jsonl

3.2 File Format
    - JSONL (JSON Lines) format
    - One JSON object per line
    - Append-only writing

================================================================================
4. API ASSUMPTIONS
================================================================================

4.1 Endpoints
    - POST /webhook - Process incoming calls
    - GET /health - Health check
    - GET /stats - System statistics
    - GET /verify - Chain verification
    - GET /incidents - List incidents

4.2 Response Format
    - status: success or error
    - data: response data
    - message: optional message

================================================================================
5. SECURITY ASSUMPTIONS
================================================================================

5.1 Tamper Evidence
    - Hash chain provides cryptographic proof
    - Any tampering detectable via verification
    - Chain of custody maintained

5.2 Data Integrity
    - SHA-256 ensures data hasn't changed
    - Prev_hash links prevent insertion/deletion
    - Timestamps provide temporal proof

================================================================================
6. DEMO ASSUMPTIONS
================================================================================

6.1 Demo Flow
    - User sends POST to /demo/webhook
    - System processes call synchronously
    - Returns immediate response
    - Logs asynchronously to disk

6.2 Demo Data
    - Simulated scam detection for presentation
    - Real hash chain for evidence
    - Beautiful formatted output

================================================================================
7. ERROR HANDLING
================================================================================

7.1 Expected Errors
    - Invalid webhook payload -> 400
    - Chain verification failure -> 500 with details
    - Missing data -> 404 with explanation

7.2 Recovery
    - Chain verification can identify broken links
    - Backups recommended for production
    - Logs are append-only for safety

================================================================================
This documentation is part of the forensic record.
Any changes to assumptions should be versioned.
================================================================================
"""
        return doc
    
    def generate_api_doc(self) -> str:
        """Generate API documentation."""
        
        doc = """
================================================================================
                    PERSON 4 - API DOCUMENTATION
================================================================================

BASE URL: http://127.0.0.1:8001 (main) / 8005 (demo)

================================================================================
ENDPOINTS
================================================================================

1. POST /webhook
   Description: Process incoming call from Exotel
   Request Body:
   - CallSid: string (required)
   - To: string (required)
   - From: string (required)
   - CallStatus: string (optional)
   
   Response:
   - status: success or error
   - data.action: block/warn/allow
   - data.risk_score: number
   - data.incident_id: string
   - data.evidence_hash: string

2. GET /health
   Description: Health check
   Response:
   - status: healthy
   - version: version number

3. GET /stats
   Description: System statistics
   Response:
   - incidents: total count
   - decisions: decision statistics
   - log_chain: chain status

4. GET /verify
   Description: Verify chain integrity
   Response:
   - valid: boolean
   - entries: number of entries
   - last_hash: last hash value

================================================================================
EXAMPLE USAGE
================================================================================

Test scam detection:
    curl -X POST http://127.0.0.1:8005/demo/webhook \\
      -H "Content-Type: application/json" \\
      -d '{"CallSid":"test","To":"+91","From":"+1"}'

Check health:
    curl http://127.0.0.1:8005/demo/status

Verify chain:
    curl http://127.0.0.1:8001/verify

================================================================================
"""
        return doc
    
    def generate_all(self):
        """Generate all documentation."""
        
        print("\n" + "="*60)
        print("📚 GENERATING DOCUMENTATION")
        print("="*60)
        
        # Assumptions doc
        assumptions = self.generate_assumptions_doc()
        assumptions_path = self.docs_dir / "assumptions.md"
        with open(assumptions_path, 'w') as f:
            f.write(assumptions)
        print(f"✅ Generated: {assumptions_path}")
        
        # API doc
        api_doc = self.generate_api_doc()
        api_path = self.docs_dir / "api_documentation.md"
        with open(api_path, 'w') as f:
            f.write(api_doc)
        print(f"✅ Generated: {api_path}")
        
        # Quick start
        quick_start = """# Quick Start Guide

## Start the Demo Server
```bash
cd person4
python final_demo.py"""