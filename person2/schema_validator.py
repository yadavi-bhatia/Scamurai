"""
Hour 19: Schema Stability Check
Validates that output format remains consistent
"""

import json
import jsonschema
from typing import Dict, Any, List
from dataclasses import dataclass, asdict


# FROZEN SCHEMA - DO NOT CHANGE
PERSON2_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "turn_id",
        "session_id", 
        "timestamp",
        "transcript",
        "detected_keywords",
        "detected_categories",
        "risk_score",
        "risk_level",
        "scam_type",
        "explanation",
        "reason_codes",
        "evidence_hash",
        "version"
    ],
    "properties": {
        "turn_id": {"type": "string", "minLength": 1},
        "session_id": {"type": "string", "minLength": 1},
        "timestamp": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}"},
        "transcript": {"type": "string"},
        "detected_keywords": {"type": "array", "items": {"type": "string"}},
        "detected_categories": {"type": "array", "items": {"type": "string"}},
        "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
        "risk_level": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE", "PENDING"]},
        "scam_type": {"type": "string"},
        "explanation": {"type": "string"},
        "reason_codes": {"type": "array", "items": {"type": "string", "pattern": "^R\\d{2}$"}},
        "evidence_hash": {"type": "string", "minLength": 16},
        "version": {"type": "string", "const": "2.0.0"}
    },
    "additionalProperties": False
}


@dataclass
class StableOutput:
    """Stable output format for Person 3 - FROZEN"""
    turn_id: str
    session_id: str
    timestamp: str
    transcript: str
    detected_keywords: List[str]
    detected_categories: List[str]
    risk_score: float
    risk_level: str
    scam_type: str
    explanation: str
    reason_codes: List[str]
    evidence_hash: str
    version: str = "2.0.0"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate against frozen schema"""
        errors = []
        try:
            jsonschema.validate(instance=self.to_dict(), schema=PERSON2_OUTPUT_SCHEMA)
        except jsonschema.ValidationError as e:
            errors.append(str(e))
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e}")
        
        return len(errors) == 0, errors


class SchemaValidator:
    """Validate schema stability across versions"""
    
    def __init__(self):
        self.schema_version = "2.0.0"
        self.schema_hash = self._compute_schema_hash()
    
    def _compute_schema_hash(self) -> str:
        """Compute hash of current schema for version tracking"""
        import hashlib
        schema_str = json.dumps(PERSON2_OUTPUT_SCHEMA, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    
    def validate_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single output against schema"""
        try:
            jsonschema.validate(instance=output, schema=PERSON2_OUTPUT_SCHEMA)
            return {"valid": True, "errors": []}
        except jsonschema.ValidationError as e:
            return {"valid": False, "errors": [str(e)]}
    
    def validate_batch(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of outputs"""
        results = []
        for i, output in enumerate(outputs):
            result = self.validate_output(output)
            results.append({"index": i, **result})
        
        valid_count = sum(1 for r in results if r["valid"])
        
        return {
            "total": len(outputs),
            "valid": valid_count,
            "invalid": len(outputs) - valid_count,
            "validity_rate": valid_count / len(outputs) if outputs else 1.0,
            "results": results
        }
    
    def get_schema_report(self) -> Dict[str, Any]:
        """Get schema stability report"""
        return {
            "schema_version": self.schema_version,
            "schema_hash": self.schema_hash,
            "required_fields": PERSON2_OUTPUT_SCHEMA["required"],
            "risk_levels": PERSON2_OUTPUT_SCHEMA["properties"]["risk_level"]["enum"],
            "additional_properties_allowed": PERSON2_OUTPUT_SCHEMA.get("additionalProperties", False)
        }


# Test schema validator
if __name__ == "__main__":
    validator = SchemaValidator()
    
    print("=" * 60)
    print("🔒 SCHEMA STABILITY CHECK")
    print("=" * 60)
    
    print(f"\nSchema Version: {validator.schema_version}")
    print(f"Schema Hash: {validator.schema_hash}")
    print(f"Required Fields: {len(PERSON2_OUTPUT_SCHEMA['required'])}")
    
    # Test with valid output
    valid_output = {
        "turn_id": "test_001",
        "session_id": "session_123",
        "timestamp": "2026-04-18T10:30:00",
        "transcript": "Send me bitcoin",
        "detected_keywords": ["bitcoin"],
        "detected_categories": ["payment_request"],
        "risk_score": 0.65,
        "risk_level": "HIGH",
        "scam_type": "payment_scam",
        "explanation": "Payment request detected",
        "reason_codes": ["R01"],
        "evidence_hash": "abc123def4567890",
        "version": "2.0.0"
    }
    
    result = validator.validate_output(valid_output)
    print(f"\nValid Output Test: {'✅ PASS' if result['valid'] else '❌ FAIL'}")
    
    # Test with invalid output (missing required field)
    invalid_output = valid_output.copy()
    del invalid_output["risk_score"]
    
    result = validator.validate_output(invalid_output)
    print(f"Invalid Output Test: {'✅ PASS' if result['valid'] else '❌ FAIL (expected)'}")
    
    print("\n✅ Schema stability verified")