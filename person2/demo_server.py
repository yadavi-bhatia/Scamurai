"""
Person 2 - Demo Server
Provides REST API for integration with Person 3
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
from linguistic_agent import LinguisticAgent

app = Flask(__name__)
CORS(app)

# Store active sessions
sessions = {}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "agent": "Person 2", "timestamp": datetime.now().isoformat()})


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze transcript text
    
    Request body:
    {
        "text": "caller said this...",
        "session_id": "optional_session_id",
        "speaker": "caller"
    }
    """
    data = request.json
    text = data.get('text', '')
    session_id = data.get('session_id', 'default')
    speaker = data.get('speaker', 'caller')
    
    # Get or create agent for this session
    if session_id not in sessions:
        sessions[session_id] = LinguisticAgent(session_id)
    
    agent = sessions[session_id]
    result = agent.analyze_transcript(text, speaker)
    
    return jsonify(result.to_dict())


@app.route('/session/<session_id>/summary', methods=['GET'])
def session_summary(session_id):
    """Get complete session summary"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    
    agent = sessions[session_id]
    return jsonify(agent.get_session_summary())


@app.route('/session/<session_id>/reset', methods=['POST'])
def reset_session(session_id):
    """Reset a session"""
    if session_id in sessions:
        sessions[session_id].reset()
    return jsonify({"status": "reset", "session_id": session_id})


@app.route('/keywords', methods=['GET'])
def get_keywords():
    """Get all scam keywords (for debugging)"""
    from linguistic_agent import ScamKeywordDatabase
    return jsonify({
        "version": ScamKeywordDatabase.VERSION,
        "total_keywords": len(ScamKeywordDatabase.get_all_keywords()),
        "keywords": ScamKeywordDatabase.KEYWORDS
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🎯 PERSON 2 - DEMO SERVER")
    print("Linguistic Pattern Agent API")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST /analyze          - Analyze transcript")
    print("  GET  /session/{id}/summary - Get session summary")
    print("  POST /session/{id}/reset  - Reset session")
    print("  GET  /keywords         - List all scam keywords")
    print("\nStarting server...")
    app.run(host='0.0.0.0', port=5001, debug=True)