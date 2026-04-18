"""
Hour 18: Improved Summary Generation
Concise, judge-friendly transcript explanations
"""

from typing import List, Dict, Any
from datetime import datetime


class SummaryGenerator:
    """Generate concise, judge-friendly summaries"""
    
    def __init__(self):
        self.risk_icons = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🔵",
            "NONE": "🟢",
            "PENDING": "⏳"
        }
    
    def generate_turn_summary(self, result: Dict[str, Any]) -> str:
        """Generate a one-line summary for a single turn"""
        risk_level = result.get("risk_level", "NONE")
        icon = self.risk_icons.get(risk_level, "⚪")
        
        if result.get("risk_score", 0) == 0:
            return f"{icon} Safe: No scam indicators"
        
        scam_type = result.get("scam_type", "unknown").replace("_", " ").title()
        keywords = result.get("detected_keywords", [])[:2]
        
        if keywords:
            return f"{icon} {risk_level}: {scam_type} (keywords: {', '.join(keywords)})"
        else:
            return f"{icon} {risk_level}: {scam_type} detected"
    
    def generate_call_summary(self, results: List[Dict[str, Any]], call_duration: int = None) -> str:
        """Generate a summary for an entire call"""
        if not results:
            return "No analysis data available"
        
        # Find highest risk
        max_risk = max([r.get("risk_score", 0) for r in results])
        highest_risk_result = max(results, key=lambda x: x.get("risk_score", 0))
        
        # Collect all keywords
        all_keywords = set()
        for r in results:
            all_keywords.update(r.get("detected_keywords", []))
        
        # Determine verdict
        if max_risk >= 0.6:
            verdict = "🚨 SCAM CONFIRMED - Immediate intervention required"
            action = "BLOCK CALL"
        elif max_risk >= 0.4:
            verdict = "⚠️ HIGH RISK - Scam likely, escalate now"
            action = "ESCALATE"
        elif max_risk >= 0.2:
            verdict = "📌 SUSPICIOUS - Monitor carefully"
            action = "MONITOR"
        else:
            verdict = "✅ SAFE - No scam detected"
            action = "NONE"
        
        # Build summary
        summary_lines = [
            f"Call Analysis Summary",
            f"{'=' * 40}",
            f"Verdict: {verdict}",
            f"Max Risk: {max_risk:.0%}",
            f"Action: {action}",
        ]
        
        if all_keywords:
            summary_lines.append(f"Keywords: {', '.join(list(all_keywords)[:5])}")
        
        if highest_risk_result.get("scam_type") and highest_risk_result["scam_type"] != "none":
            summary_lines.append(f"Scam Type: {highest_risk_result['scam_type'].replace('_', ' ').title()}")
        
        if call_duration:
            summary_lines.append(f"Duration: {call_duration}s")
        
        return "\n".join(summary_lines)
    
    def generate_judge_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a judge-friendly summary card"""
        return {
            "verdict": session_data.get("final_verdict", "UNKNOWN"),
            "risk_score": session_data.get("max_risk_score", 0),
            "risk_level": session_data.get("risk_level", "UNKNOWN"),
            "scam_type": session_data.get("scam_type", "none"),
            "key_indicators": session_data.get("unique_keywords_detected", [])[:5],
            "explanation": session_data.get("explanation", ""),
            "recommended_action": session_data.get("recommended_action", "REVIEW"),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_console_output(self, result: Dict[str, Any]) -> str:
        """Generate colorful console output for demo"""
        risk_score = result.get("risk_score", 0)
        
        # Create visual risk bar
        bar_length = 20
        filled = int(risk_score * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Determine color
        if risk_score >= 0.6:
            color_prefix = "\033[91m"  # Red
        elif risk_score >= 0.4:
            color_prefix = "\033[93m"  # Yellow
        elif risk_score >= 0.2:
            color_prefix = "\033[94m"  # Blue
        else:
            color_prefix = "\033[92m"  # Green
        
        reset = "\033[0m"
        
        return f"{color_prefix}Risk: [{bar}] {risk_score:.0%}{reset}"


# Quick test
if __name__ == "__main__":
    generator = SummaryGenerator()
    
    # Test with sample result
    sample_result = {
        "risk_score": 0.65,
        "risk_level": "HIGH",
        "scam_type": "payment_scam",
        "detected_keywords": ["bitcoin", "immediately", "send money"]
    }
    
    print(generator.generate_turn_summary(sample_result))
    print("\n" + generator.generate_console_output(sample_result))