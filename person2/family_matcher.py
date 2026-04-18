"""
PERSON 2 - FAMILY VOICE MATCHER (Hour 26)
Support multiple reference samples for family members
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class FamilyMember:
    """Represents a family member with voice reference"""
    id: str
    name: str
    relationship: str
    reference_hash: str
    voice_features: Optional[Dict] = None
    is_trusted: bool = True


@dataclass
class VoiceMatchResult:
    """Result of voice comparison against family references"""
    matched_member: Optional[FamilyMember]
    similarity_score: float
    confidence: float
    is_family_match: bool
    match_type: str  # "exact", "partial", "none"
    notes: str


class FamilyVoiceMatcher:
    """
    Supports multiple reference samples for family members
    Used for family impersonation detection
    """
    
    def __init__(self):
        self.family_members: Dict[str, FamilyMember] = {}
        self.version = "1.0.0"
        print("[FAMILY] Family voice matcher ready")
    
    def add_family_member(self, name: str, relationship: str, reference_features: Dict) -> str:
        """
        Add a family member's voice reference
        
        Args:
            name: Member's name
            relationship: e.g., "mother", "father", "son", "daughter"
            reference_features: Voice embedding/features from Person 1
        """
        member_id = hashlib.md5(f"{name}{relationship}".encode()).hexdigest()[:8]
        
        self.family_members[member_id] = FamilyMember(
            id=member_id,
            name=name,
            relationship=relationship,
            reference_hash=hashlib.sha256(str(reference_features).encode()).hexdigest()[:16],
            voice_features=reference_features,
            is_trusted=True
        )
        
        print(f"[FAMILY] Added: {name} ({relationship}) - ID: {member_id}")
        return member_id
    
    def remove_family_member(self, member_id: str) -> bool:
        """Remove a family member"""
        if member_id in self.family_members:
            del self.family_members[member_id]
            print(f"[FAMILY] Removed member: {member_id}")
            return True
        return False
    
    def match_voice(self, current_features: Dict) -> VoiceMatchResult:
        """
        Compare current voice against all family references
        
        Returns:
            VoiceMatchResult with best match info
        """
        if not self.family_members:
            return VoiceMatchResult(
                matched_member=None,
                similarity_score=0.0,
                confidence=0.0,
                is_family_match=False,
                match_type="none",
                notes="No family references available"
            )
        
        best_match = None
        best_score = 0.0
        
        # In production, this would use actual voice embedding comparison
        # For demo, we simulate based on available data
        for member in self.family_members.values():
            # Placeholder: Actual voice similarity calculation
            # similarity = self._calculate_similarity(current_features, member.voice_features)
            
            # Simulated similarity (replace with actual comparison)
            similarity = 0.0
            
            if similarity > best_score:
                best_score = similarity
                best_match = member
        
        if best_score >= 0.7:
            match_type = "exact"
            is_match = True
            notes = f"Voice matches {best_match.name} ({best_match.relationship})"
        elif best_score >= 0.4:
            match_type = "partial"
            is_match = True
            notes = f"Partial voice match with {best_match.name} - low confidence"
        else:
            match_type = "none"
            is_match = False
            notes = "No family voice match detected - possible impersonation"
        
        return VoiceMatchResult(
            matched_member=best_match,
            similarity_score=round(best_score, 3),
            confidence=round(best_score * 0.9, 3),
            is_family_match=is_match,
            match_type=match_type,
            notes=notes
        )
    
    def get_all_family_members(self) -> List[Dict]:
        """Get all registered family members"""
        return [
            {
                "id": m.id,
                "name": m.name,
                "relationship": m.relationship,
                "is_trusted": m.is_trusted
            }
            for m in self.family_members.values()
        ]
    
    def get_match_explanation(self, match_result: VoiceMatchResult) -> str:
        """Get judge-friendly explanation of voice match"""
        if not match_result.is_family_match:
            if match_result.match_type == "none":
                return "Voice does not match any family member - possible impersonation"
            return "No family voice match detected"
        
        if match_result.matched_member:
            return f"Voice matches {match_result.matched_member.name} ({match_result.matched_member.relationship}) with {match_result.similarity_score:.0%} confidence"
        
        return "Voice matches a family member"


if __name__ == "__main__":
    matcher = FamilyVoiceMatcher()
    
    # Add family members
    matcher.add_family_member("Rajesh", "father", {"features": "mock"})
    matcher.add_family_member("Priya", "mother", {"features": "mock"})
    
    # Test matching
    result = matcher.match_voice({"features": "mock_test"})
    print("Match result:", result)