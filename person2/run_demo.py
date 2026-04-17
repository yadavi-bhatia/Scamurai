"""
Quick demo script for judges
Shows the linguistic agent in action with clear output
"""

import json
from linguistic_agent import LinguisticAgent

def main():
    print("\n" + "=" * 60)
    print("🎯 LINGUISTIC AGENT DEMO")
    print("Multi-Agent Defense System - Person 3")
    print("=" * 60)
    
    agent = LinguisticAgent(use_mock_asr=True)
    
    # Demo scenarios
    demos = [
        {
            "name": "SCENARIO A: Real Customer Call",
            "transcript": """
            Hi there, um, I'm calling because I think there's a mistake on my bill.
            Let me see... actually, it looks like I was charged twice last month.
            Could you please help me understand what happened? Thank you.
            """,
            "expected": "Human"
        },
        {
            "name": "SCENARIO B: AI Scam Call",
            "transcript": """
            This is an urgent security alert. Do not hang up.
            Your social security number has been compromised.
            You must buy $500 in Bitcoin immediately to secure your account.
            Do not tell anyone about this call.
            """,
            "expected": "Scam"
        },
        {
            "name": "SCENARIO C: Confused Human (Not Scam)",
            "transcript": """
            Um, hello? I got a call about... wait, let me remember.
            Actually, I think it was about my credit card.
            I'm not really sure. Maybe I should call the number on the back instead.
            """,
            "expected": "Human"
        }
    ]
    
    for demo in demos:
        print(f"\n📞 {demo['name']}")
        print(f"   Expected: {demo['expected']}")
        print("-" * 50)
        
        result = agent.analyze_text_transcript(demo['transcript'])
        
        # Color coding
        risk = result['linguistic_risk_score']
        if risk > 0.65:
            verdict_icon = "🔴"
            verdict_text = "SCAM LIKELY"
        elif risk < 0.35:
            verdict_icon = "🟢"
            verdict_text = "HUMAN LIKELY"
        else:
            verdict_icon = "🟡"
            verdict_text = "UNCERTAIN - ESCALATE"
        
        print(f"   {verdict_icon} Verdict: {verdict_text}")
        print(f"   Risk Score: {risk}")
        print(f"   Scam Phrases: {result['scam_phrase_count']}")
        print(f"   Urgency: {result['urgency_level']}")
        print(f"   Human Indicators: {', '.join(result['human_speech_indicators']) if result['human_speech_indicators'] else 'none'}")
        print(f"   Notes: {result['notes']}")
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete")
    print("Key takeaway: Linguistic agent detects patterns")
    print("even when voice biometrics can't (poor audio).")
    print("=" * 60)


if __name__ == "__main__":
    main()