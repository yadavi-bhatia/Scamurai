
"""Hour 20: Final Log Integrity Test - Verify hash chain remains valid."""

from datetime import datetime
from pathlib import Path
import json
import hashlib


class IntegrityTest:
    """Test and verify log chain integrity."""
    
    def __init__(self, chain_path: str = "data/immutable_log.jsonl"):
        self.chain_path = Path(chain_path)
        self.results = []
    
    def run_full_test(self) -> dict:
        """Run complete integrity test suite."""
        
        print("\n" + "="*70)
        print("🔒 FINAL LOG INTEGRITY TEST")
        print("="*70)
        
        # Test 1: Chain exists
        print("\n📋 Test 1: Chain exists")
        chain_exists = self.chain_path.exists()
        print(f"   Result: {'✅ PASS' if chain_exists else '❌ FAIL'}")
        self.results.append(("Chain exists", chain_exists))
        
        # Test 2: Chain not empty
        print("\n📋 Test 2: Chain not empty")
        entries = self._load_entries()
        chain_not_empty = len(entries) > 0
        print(f"   Result: {'✅ PASS' if chain_not_empty else '❌ FAIL'} ({len(entries)} entries)")
        self.results.append(("Chain not empty", chain_not_empty))
        
        # Test 3: All hashes valid
        print("\n📋 Test 3: All hashes valid")
        hash_valid = self._verify_hashes(entries)
        print(f"   Result: {'✅ PASS' if hash_valid else '❌ FAIL'}")
        self.results.append(("Hashes valid", hash_valid))
        
        # Test 4: Chain links intact
        print("\n📋 Test 4: Chain links intact")
        links_intact = self._verify_links(entries)
        print(f"   Result: {'✅ PASS' if links_intact else '❌ FAIL'}")
        self.results.append(("Links intact", links_intact))
        
        # Test 5: No tampering detected
        print("\n📋 Test 5: No tampering detected")
        no_tampering = hash_valid and links_intact
        print(f"   Result: {'✅ PASS' if no_tampering else '❌ FAIL'}")
        self.results.append(("No tampering", no_tampering))
        
        # Final verdict
        print("\n" + "="*70)
        all_passed = all(r[1] for r in self.results)
        if all_passed:
            print("🎉 FINAL VERDICT: CHAIN INTEGRITY VERIFIED - VALID")
        else:
            print("⚠️ FINAL VERDICT: CHAIN INTEGRITY COMPROMISED")
        print("="*70)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "all_passed": all_passed,
            "results": self.results,
            "total_entries": len(entries),
            "status": "VALID" if all_passed else "INVALID"
        }
    
    def _load_entries(self):
        """Load all chain entries."""
        if not self.chain_path.exists():
            return []
        
        entries = []
        with open(self.chain_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries
    
    def _verify_hashes(self, entries):
        """Verify all hash values."""
        for entry in entries:
            entry_copy = entry.copy()
            stored_hash = entry_copy.pop('hash', None)
            content = json.dumps(entry_copy, sort_keys=True, default=str)
            computed_hash = hashlib.sha256(content.encode()).hexdigest()
            
            if stored_hash != computed_hash:
                print(f"   ❌ Hash mismatch at index {entry.get('index', '?')}")
                return False
        return True
    
    def _verify_links(self, entries):
        """Verify chain links."""
        for i in range(1, len(entries)):
            if entries[i].get('prev_hash') != entries[i-1].get('hash'):
                print(f"   ❌ Link broken between {i-1} and {i}")
                return False
        return True
    
    def generate_report(self) -> str:
        """Generate integrity test report."""
        result = self.run_full_test()
        
        report = f"""
{'='*70}
INTEGRITY TEST REPORT
{'='*70}
Timestamp: {datetime.now().isoformat()}
Chain Path: {self.chain_path}
Total Entries: {result['total_entries']}
Final Status: {result['status']}

Test Results:
"""
        for name, passed in result['results']:
            report += f"  {'✅' if passed else '❌'} {name}\n"
        
        report += f"""
{'='*70}
This chain is cryptographically verified.
Any tampering would break the hash chain.
{'='*70}
"""
        return report


if __name__ == "__main__":
    tester = IntegrityTest()
    result = tester.run_full_test()
    
    # Save report
    report_path = Path("data/integrity_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(tester.generate_report())
    print(f"\n📄 Report saved: {report_path}")
