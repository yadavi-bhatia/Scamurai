
"""Hour 16: Alert/Report Actions - Action hooks for notifications."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import json
from pathlib import Path


class AlertLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertAction:
    """Action hooks for alerts and reporting."""
    
    def __init__(self, alert_log_path: str = "data/alerts.jsonl"):
        self.alert_log_path = Path(alert_log_path)
        self.alert_log_path.parent.mkdir(parents=True, exist_ok=True)
        self._alerts: List[Dict] = []
        self._load_alerts()
    
    def _load_alerts(self):
        if not self.alert_log_path.exists():
            return
        with open(self.alert_log_path, 'r') as f:
            for line in f:
                if line.strip():
                    self._alerts.append(json.loads(line))
    
    def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        incident_id: str = "",
        call_id: str = ""
    ) -> Dict[str, Any]:
        """Send an alert (console, webhook, or file)."""
        
        alert = {
            "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "title": title,
            "message": message,
            "incident_id": incident_id,
            "call_id": call_id
        }
        
        self._alerts.append(alert)
        with open(self.alert_log_path, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # Print with formatting
        if level == AlertLevel.CRITICAL:
            print(f"\n🔴 CRITICAL: {title} - {message}")
        elif level == AlertLevel.WARNING:
            print(f"\n🟡 WARNING: {title} - {message}")
        else:
            print(f"\n🔵 INFO: {title} - {message}")
        
        return alert
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        return self._alerts[-limit:] if self._alerts else []
    
    def get_critical_alerts(self) -> List[Dict]:
        return [a for a in self._alerts if a.get('level') == 'CRITICAL']


if __name__ == "__main__":
    print("✅ Hour 16: alert_actions.py ready")
