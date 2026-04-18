
"""Hour 12: Incident Storage - Store first incident record."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json


class IncidentStorage:
    """Store and retrieve incident records."""
    
    def __init__(self, storage_path: str = "data/incidents.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._incidents: List[Dict] = []
        self._load_incidents()
    
    def _load_incidents(self):
        if not self.storage_path.exists():
            return
        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    self._incidents.append(json.loads(line))
    
    def store_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a complete incident record."""
        record = {
            "incident_id": f"inc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().isoformat(),
            "data": incident_data,
            "version": "1.0.0"
        }
        self._incidents.append(record)
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(record) + '\n')
        print(f"📝 Incident stored: {record['incident_id']}")
        return record
    
    def get_incident(self, incident_id: str) -> Optional[Dict]:
        for incident in self._incidents:
            if incident.get('incident_id') == incident_id:
                return incident
        return None
    
    def get_all_incidents(self) -> List[Dict]:
        return self._incidents.copy()


if __name__ == "__main__":
    print("✅ Hour 12: incident_storage.py ready")
