"""
Person 2 - Configuration
Indian context settings for scam detection
"""

# Scam detection thresholds (adjusted for Indian context)
RISK_THRESHOLDS = {
    "critical": 0.65,  # SCAM CONFIRMED - Block immediately
    "high": 0.45,      # SCAM LIKELY - Escalate to human
    "medium": 0.25,    # SUSPICIOUS - Monitor carefully
    "low": 0.08        # CAUTION - Review later
}

# ASR Configuration (Speech-to-Text)
ASR_CONFIG = {
    "engine": "google",      # Options: google, whisper, assemblyai, azure
    "sample_rate": 16000,    # 16kHz for telephony quality
    "chunk_duration": 3,     # Process 3-second chunks
    "language": "hi-IN",     # Hindi + Indian English
    "energy_threshold": 300,  # Minimum audio energy for speech detection
    "pause_threshold": 0.8,   # Seconds of silence to indicate phrase end
    "phrase_threshold": 0.3   # Minimum phrase length
}

# Evidence storage
EVIDENCE_CONFIG = {
    "save_transcripts": True,
    "save_audio_chunks": False,
    "save_high_risk_only": True,
    "output_dir": "./evidence",
    "max_evidence_per_session": 50,
    "retention_days": 30
}

# Scam categories with weights and colors
SCAM_CATEGORIES = {
    "payment_request": {"weight": 0.40, "color": "🔴", "description": "Payment or money transfer requested"},
    "identity_theft": {"weight": 0.35, "color": "🔴", "description": "Personal/identifying information requested"},
    "threat": {"weight": 0.30, "color": "🟠", "description": "Threatening or intimidating language"},
    "urgency": {"weight": 0.22, "color": "🟡", "description": "Artificial urgency or pressure tactics"},
    "fake_authority": {"weight": 0.18, "color": "🟡", "description": "Impersonation of authority figure"},
    "scam_phrases": {"weight": 0.12, "color": "🔵", "description": "Known scam phrase patterns"}
}

# Alert configuration
ALERT_CONFIG = {
    "webhook_url": None,  # Optional: URL to send alerts
    "dashboard_update_interval": 1,  # Seconds between dashboard updates
    "sound_alert_on_critical": True,
    "show_popup_on_high_risk": True
}

# Logging configuration
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "./logs/person2.log",
    "max_bytes": 10485760,  # 10MB
    "backup_count": 5
}

# API configuration (for demo server)
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 5001,
    "debug": True,
    "cors_origins": ["http://localhost:3000", "http://localhost:5000"]
}