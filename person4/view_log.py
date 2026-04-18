"""View and verify the audit log."""

import json
from pathlib import Path
from tamper_log import TamperEvidentLog

def view_log():
    log = TamperEvidentLog()
    
    print("\n" + "="*80)
    print("🔍 AUDIT CHAIN LOG SUMMARY")
    print("="*80)
    
    if not log.log_path.exists():
        print("❌ Log file not found!")
        return
    
    with open(log.log_path, 'r') as f:
        lines = f.readlines()
    
    print(f"\n📁 Log file: {log.log_path.absolute()}")
    print(f"📊 Total entries: {len(lines)}")
    print(f"🔒 Chain verification: {log.verify_chain()[0]}")
    
    print("\n" + "="*80)
    print("ENTRIES:")
    print("="*80)
    
    for i, line in enumerate(lines, 1):
        try:
            data = json.loads(line)
            print(f"\n[{i}] Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"    Risk: {data.get('final_risk', 'N/A')}")
            print(f"    Score: {data.get('final_score', 'N/A')}")
            print(f"    Caller: {data.get('caller_type', 'N/A')}")
            print(f"    Hash: {data.get('hash', 'N/A')[:16]}...")
            
            # Show reason codes if present
            if 'reason_codes' in data:
                codes = data['reason_codes'][:3]
                print(f"    Reasons: {', '.join(codes)}")
                
        except Exception as e:
            print(f"\n[{i}] Error parsing: {e}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    view_log()