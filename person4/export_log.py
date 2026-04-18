import json
import csv

with open('data/logs/audit_chain.log', 'r') as f:
    records = [json.loads(line) for line in f]

with open('audit_export.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['timestamp', 'final_risk', 'final_score', 'caller_type', 'hash'])
    writer.writeheader()
    for r in records:
        writer.writerow({
            'timestamp': r.get('timestamp'),
            'final_risk': r.get('final_risk'),
            'final_score': r.get('final_score'),
            'caller_type': r.get('caller_type'),
            'hash': r.get('hash', '')[:16]
        })

print(f'Exported {len(records)} records to audit_export.csv')
