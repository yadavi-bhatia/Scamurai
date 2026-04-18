"""
Person 2 - Demo Runner for Defend & Detect
Tests all scam scenarios and produces output for Person 3
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
from reason_codes import ReasonCodeGenerator
from summary_generator import SummaryGenerator
from frozen_handoff import FrozenHandoffGenerator
from test_mixed_calls import MixedCallValidator

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linguistic_agent import LinguisticAgent
from demo_transcripts import DEMO_SCENARIOS


class Person2DemoRunner:
    """Run Person 2 on all demo scenarios"""
    
    def __init__(self):
        self.agent = LinguisticAgent("demo_session")
        self.results = {}
    
    def analyze_transcript_scenario(self, scenario_name: str, data: Dict) -> Dict[str, Any]:
        """Analyze a full transcript scenario"""
        transcript = data.get("transcript", "")
        expected_risk = data.get("expected_risk", "UNKNOWN")
        description = data.get("description", "")
        
        # Combine all speaker lines
        full_text = transcript.replace("Caller:", "").replace("Victim:", "").strip()
        
        # Analyze with Person 2
        result = self.agent.analyze_transcript(full_text)
        
        # Map Person 2 risk level to expected format
        risk_mapping = {
            "CRITICAL": "DANGEROUS",
            "HIGH": "DANGEROUS",
            "MEDIUM": "SUSPICIOUS",
            "LOW": "LOW_RISK",
            "NONE": "SAFE"
        }
        
        actual_risk = risk_mapping.get(result.risk_level, "UNKNOWN")
        
        return {
            "scenario": scenario_name,
            "name": data.get("name", scenario_name),
            "description": description,
            "expected_risk": expected_risk,
            "actual_risk": actual_risk,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "scam_type": result.scam_type,
            "detected_keywords": result.detected_keywords,
            "detected_categories": result.detected_categories,
            "explanation": result.explanation,
            "reason_codes": result.reason_codes,
            "passed": actual_risk == expected_risk
        }
    
    def analyze_streaming_scenario(self, chunks: List[tuple]) -> Dict[str, Any]:
        """Analyze a streaming scenario with partial chunks"""
        results = []
        max_risk = 0.0
        alert_triggered_at = None
        
        for i, (speaker, text) in enumerate(chunks):
            # Analyze each chunk
            result = self.agent.analyze_transcript(text)
            results.append({
                "chunk": i + 1,
                "speaker": speaker,
                "text": text,
                "risk_score": result.risk_score,
                "risk_level": result.risk_level,
                "detected_keywords": result.detected_keywords
            })
            
            if result.risk_score > max_risk:
                max_risk = result.risk_score
            
            # Check if alert would trigger at this chunk
            if result.risk_score >= 0.4 and alert_triggered_at is None:
                alert_triggered_at = i + 1
        
        # Determine final risk
        if max_risk >= 0.6:
            final_risk = "DANGEROUS"
        elif max_risk >= 0.3:
            final_risk = "SUSPICIOUS"
        elif max_risk >= 0.1:
            final_risk = "LOW_RISK"
        else:
            final_risk = "SAFE"
        
        return {
            "type": "streaming",
            "chunks_analyzed": len(chunks),
            "max_risk_score": round(max_risk, 3),
            "final_risk": final_risk,
            "alert_triggered_at_chunk": alert_triggered_at,
            "chunk_results": results
        }
    
    def validate_detection_accuracy(self) -> Dict[str, Any]:
        """Validate detection accuracy on synthetic scam transcripts"""
        print("\n" + "=" * 80)
        print("📊 VALIDATION: Scam Detection Accuracy")
        print("=" * 80)
        
        # Define expected outcomes for each scenario
        expected_outcomes = {
            "safe_amazon_call": {"risk": "SAFE", "min_score": 0.0, "max_score": 0.1},
            "bank_kyc_scam": {"risk": "DANGEROUS", "min_score": 0.4, "max_score": 1.0},
            "hinglish_police_scam": {"risk": "DANGEROUS", "min_score": 0.4, "max_score": 1.0},
            "courier_scam": {"risk": "DANGEROUS", "min_score": 0.4, "max_score": 1.0},
            "normal_family_call": {"risk": "SAFE", "min_score": 0.0, "max_score": 0.1}
        }
        
        results = []
        
        for scenario_name, expected in expected_outcomes.items():
            if scenario_name in DEMO_SCENARIOS:
                data = DEMO_SCENARIOS[scenario_name]
                transcript = data.get("transcript", "")
                full_text = transcript.replace("Caller:", "").replace("Victim:", "").strip()
                
                result = self.agent.analyze_transcript(full_text)
                
                # Determine if detection is correct
                risk_mapping = {"CRITICAL": "DANGEROUS", "HIGH": "DANGEROUS", 
                               "MEDIUM": "SUSPICIOUS", "LOW": "LOW_RISK", "NONE": "SAFE"}
                actual_risk = risk_mapping.get(result.risk_level, "UNKNOWN")
                
                score_correct = expected["min_score"] <= result.risk_score <= expected["max_score"]
                risk_correct = actual_risk == expected["risk"]
                
                results.append({
                    "scenario": scenario_name,
                    "expected_risk": expected["risk"],
                    "actual_risk": actual_risk,
                    "risk_score": result.risk_score,
                    "score_correct": score_correct,
                    "risk_correct": risk_correct,
                    "passed": score_correct and risk_correct
                })
        
        # Calculate accuracy
        passed = sum(1 for r in results if r["passed"])
        accuracy = (passed / len(results)) * 100 if results else 0
        
        print(f"\n📈 Validation Results:")
        print(f"   Total scenarios: {len(results)}")
        print(f"   Passed: {passed}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        for r in results:
            status = "✅" if r["passed"] else "❌"
            print(f"   {status} {r['scenario']}: {r['actual_risk']} (score: {r['risk_score']:.0%})")
        
        return {
            "accuracy": accuracy,
            "passed": passed,
            "total": len(results),
            "details": results
        }
    
    def run_all(self):
        """Run all demo scenarios"""
        print("=" * 80)
        print("🎯 PERSON 2 - DEMO RUNNER")
        print("Defend & Detect: Real-Time Scam Call Shield")
        print("=" * 80)
        
        # Test transcript scenarios
        transcript_scenarios = ["safe_amazon_call", "bank_kyc_scam", "hinglish_police_scam", "courier_scam", "normal_family_call"]
        
        print("\n📝 ANALYZING TRANSCRIPT SCENARIOS\n")
        print("-" * 80)
        
        passed = 0
        for scenario_name in transcript_scenarios:
            if scenario_name in DEMO_SCENARIOS:
                data = DEMO_SCENARIOS[scenario_name]
                result = self.analyze_transcript_scenario(scenario_name, data)
                self.results[scenario_name] = result
                
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(f"\n{status} | {result['name']}")
                print(f"   Expected: {result['expected_risk']} | Actual: {result['actual_risk']}")
                print(f"   Risk Score: {result['risk_score']:.0%} | Level: {result['risk_level']}")
                print(f"   Scam Type: {result['scam_type']}")
                print(f"   Keywords: {', '.join(result['detected_keywords'][:5])}")
                print(f"   Categories: {result['detected_categories']}")
                print(f"   Explanation: {result['explanation'][:100]}...")
                
                if result["passed"]:
                    passed += 1
        
        # Test streaming scenario
        if "escalating_tech_support" in DEMO_SCENARIOS:
            print("\n" + "-" * 80)
            print("\n🌊 ANALYZING STREAMING SCENARIO (Real-time chunks)\n")
            print("-" * 80)
            
            streaming_data = DEMO_SCENARIOS["escalating_tech_support"]
            chunks = streaming_data.get("chunks", [])
            result = self.analyze_streaming_scenario(chunks)
            self.results["escalating_tech_support"] = result
            
            print(f"\n📞 Scenario: {streaming_data['name']}")
            print(f"   Expected: {streaming_data['expected_risk']} | Final Risk: {result['final_risk']}")
            print(f"   Alert triggered at chunk: {result['alert_triggered_at_chunk']}")
            print("\n   Chunk-by-chunk analysis:")
            for chunk in result["chunk_results"]:
                alert_marker = " 🚨" if chunk["risk_score"] >= 0.4 else ""
                print(f"      Chunk {chunk['chunk']}: '{chunk['text'][:50]}...' → Risk: {chunk['risk_score']:.0%}{alert_marker}")
        
        # Run validation
        validation = self.validate_detection_accuracy()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 DEMO SUMMARY")
        print("=" * 80)
        print(f"Transcript scenarios passed: {passed}/{len(transcript_scenarios)}")
        print(f"Validation accuracy: {validation['accuracy']:.1f}%")
        
        # Final output for Person 3
        print("\n📤 FINAL OUTPUT FOR PERSON 3 (Consensus Agent):")
        print("=" * 80)
        
        for scenario, result in self.results.items():
            if "chunks" not in str(result):
                output = {
                    "session_id": f"demo_{scenario}",
                    "call_type": result.get("name", scenario),
                    "risk_assessment": {
                        "score": result["risk_score"],
                        "level": result["actual_risk"],
                        "scam_type": result["scam_type"],
                        "explanation": result["explanation"],
                        "reason_codes": result["reason_codes"]
                    },
                    "evidence": {
                        "keywords": result["detected_keywords"],
                        "categories": result["detected_categories"],
                        "transcript_excerpt": result.get("description", "")[:100]
                    },
                    "verdict_match": result["passed"],
                    "timestamp": datetime.now().isoformat()
                }
                print(f"\n📞 {scenario.upper().replace('_', ' ')}:")
                print(json.dumps(output, indent=2))
        
        return validation
    
    def export_for_person3(self) -> Dict:
        """Export results in format expected by Person 3"""
        export = {
            "agent": "Person 2 - Linguistic Pattern Agent",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "scenarios_tested": len(self.results),
            "results": []
        }
        
        for scenario, result in self.results.items():
            if "chunks" not in str(result):
                export["results"].append({
                    "scenario": scenario,
                    "risk_score": result["risk_score"],
                    "risk_level": result["actual_risk"],
                    "scam_type": result["scam_type"],
                    "detected_keywords": result["detected_keywords"],
                    "detected_categories": result["detected_categories"],
                    "explanation": result["explanation"],
                    "reason_codes": result["reason_codes"]
                })
        
        return export

        def run_final_validation(self):
            """Run all validations for Hours 16-20"""
            print("\n" + "=" * 80)
            print("🏁 FINAL VALIDATION (Hours 16-20)")
            print("=" * 80)
            
            # 1. Mixed call validation
            mixed_validator = MixedCallValidator()
            mixed_results = mixed_validator.run_validation()
            
            # 2. Generate frozen handoff
            handoff_gen = FrozenHandoffGenerator()
            
            # Collect all results
            all_results = []
            for scenario, result in self.results.items():
                if "chunks" not in str(result):
                    all_results.append({
                        "risk_score": result["risk_score"],
                        "risk_level": result["risk_level"],
                        "detected_keywords": result["detected_keywords"],
                        "detected_categories": result["detected_categories"],
                        "scam_type": result["scam_type"],
                        "explanation": result["explanation"],
                        "evidence_hash": f"hash_{scenario}"
                    })
            
            # Create frozen handoff for Person 3
            handoff = handoff_gen.create_handoff(
                session_id="final_demo",
                call_id="DEMO_CALL_001",
                detection_results=all_results
            )
            
            print("\n📤 FROZEN HANDOFF FOR PERSON 3:")
            print(handoff.to_json())
            
            # Save handoff
            with open("handoff_for_person3.json", "w") as f:
                f.write(handoff.to_json())
            
            return handoff


def main():
    """Main entry point"""
    runner = Person2DemoRunner()
    validation = runner.run_all()
    
    # Save results for Person 3
    with open("person2_output.json", "w") as f:
        json.dump(runner.export_for_person3(), f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ Person 2 demo complete!")
    print(f"📊 Validation Accuracy: {validation['accuracy']:.1f}%")
    print("📁 Results saved to: person2_output.json")
    print("📤 Ready for Person 3 (Consensus Agent)")
    print("=" * 80)


if __name__ == "__main__":
    main()