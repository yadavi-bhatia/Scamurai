"""
Hour 17: Tuned Reason Codes
Clear, standardized explanation categories for Person 3
"""

from enum import Enum
from typing import List, Dict, Any


class ReasonCode(str, Enum):
    """Standardized reason codes for scam detection"""
    
    # Payment-related scams (R01-R09)
    R01_CRYPTO_PAYMENT = "R01"
    R02_GIFT_CARD = "R02"
    R03_WIRE_TRANSFER = "R03"
    R04_UPI_PAYMENT = "R04"
    R05_PAYMENT_URGENCY = "R05"
    R06_LARGE_AMOUNT = "R06"
    R07_REPEATED_PAYMENT = "R07"
    R08_FOREIGN_PAYMENT = "R08"
    R09_PAYMENT_TO_UNKNOWN = "R09"
    
    # Identity theft (R10-R19)
    R10_OTP_REQUEST = "R10"
    R11_AADHAAR_REQUEST = "R11"
    R12_PAN_REQUEST = "R12"
    R13_BANK_DETAILS = "R13"
    R14_PASSWORD_REQUEST = "R14"
    R15_PIN_REQUEST = "R15"
    R16_SSN_REQUEST = "R16"
    R17_DOB_REQUEST = "R17"
    R18_ADDRESS_REQUEST = "R18"
    R19_FAMILY_DETAILS = "R19"
    
    # Threats (R20-R29)
    R20_ARREST_THREAT = "R20"
    R21_LEGAL_ACTION = "R21"
    R22_ACCOUNT_FREEZE = "R22"
    R23_POLICE_THREAT = "R23"
    R24_COURT_SUMMONS = "R24"
    R25_FINE_PENALTY = "R25"
    R26_DEPORTATION = "R26"
    R27_BLACKLIST = "R27"
    R28_CREDIT_DAMAGE = "R28"
    R29_FAMILY_THREAT = "R29"
    
    # Urgency/Pressure (R30-R39)
    R30_TIME_PRESSURE = "R30"
    R31_DONT_HANG_UP = "R31"
    R32_LIMITED_TIME = "R32"
    R33_FINAL_WARNING = "R33"
    R34_EXPIRING_NOW = "R34"
    R35_ACT_NOW = "R35"
    R36_NO_TIME_TO_THINK = "R36"
    R37_SPECIAL_OFFER = "R37"
    R38_ONE_TIME_DEAL = "R38"
    R39_LAST_CHANCE = "R39"
    
    # Fake Authority (R40-R49)
    R40_GOVERNMENT_OFFICIAL = "R40"
    R41_BANK_OFFICIAL = "R41"
    R42_POLICE_OFFICIAL = "R42"
    R43_TECH_SUPPORT = "R43"
    R44_COURIER_OFFICIAL = "R44"
    R45_TAX_OFFICIAL = "R45"
    R46_LEGAL_OFFICIAL = "R46"
    R47_MEDICAL_OFFICIAL = "R47"
    R48_UTILITY_OFFICIAL = "R48"
    R49_CHARITY_REPRESENTATIVE = "R49"
    
    # Scam Phrases (R50-R59)
    R50_ACCOUNT_COMPROMISED = "R50"
    R51_SUSPICIOUS_ACTIVITY = "R51"
    R52_SECURITY_ALERT = "R52"
    R53_FRAUD_ALERT = "R53"
    R54_VERIFY_IDENTITY = "R54"
    R55_UPDATE_RECORDS = "R55"
    R56_WINNING_PRIZE = "R56"
    R57_VIRUS_DETECTED = "R57"
    R58_REFUND_PROCESS = "R58"
    R59_OVERPAYMENT = "R59"


# Mapping from detection categories to reason codes
CATEGORY_TO_REASON_CODES = {
    "payment_request": [
        ReasonCode.R01_CRYPTO_PAYMENT,
        ReasonCode.R02_GIFT_CARD,
        ReasonCode.R03_WIRE_TRANSFER,
        ReasonCode.R04_UPI_PAYMENT
    ],
    "identity_theft": [
        ReasonCode.R10_OTP_REQUEST,
        ReasonCode.R11_AADHAAR_REQUEST,
        ReasonCode.R12_PAN_REQUEST,
        ReasonCode.R13_BANK_DETAILS,
        ReasonCode.R14_PASSWORD_REQUEST
    ],
    "threat": [
        ReasonCode.R20_ARREST_THREAT,
        ReasonCode.R21_LEGAL_ACTION,
        ReasonCode.R22_ACCOUNT_FREEZE,
        ReasonCode.R23_POLICE_THREAT
    ],
    "urgency": [
        ReasonCode.R30_TIME_PRESSURE,
        ReasonCode.R31_DONT_HANG_UP,
        ReasonCode.R32_LIMITED_TIME,
        ReasonCode.R33_FINAL_WARNING
    ],
    "fake_authority": [
        ReasonCode.R40_GOVERNMENT_OFFICIAL,
        ReasonCode.R41_BANK_OFFICIAL,
        ReasonCode.R42_POLICE_OFFICIAL,
        ReasonCode.R43_TECH_SUPPORT
    ],
    "scam_phrases": [
        ReasonCode.R50_ACCOUNT_COMPROMISED,
        ReasonCode.R51_SUSPICIOUS_ACTIVITY,
        ReasonCode.R52_SECURITY_ALERT,
        ReasonCode.R53_FRAUD_ALERT
    ]
}


# Keyword to specific reason code mapping
KEYWORD_TO_REASON_CODE = {
    # Payment keywords
    "bitcoin": ReasonCode.R01_CRYPTO_PAYMENT,
    "crypto": ReasonCode.R01_CRYPTO_PAYMENT,
    "gift card": ReasonCode.R02_GIFT_CARD,
    "giftcard": ReasonCode.R02_GIFT_CARD,
    "wire transfer": ReasonCode.R03_WIRE_TRANSFER,
    "google pay": ReasonCode.R04_UPI_PAYMENT,
    "phonepe": ReasonCode.R04_UPI_PAYMENT,
    
    # Identity keywords
    "otp": ReasonCode.R10_OTP_REQUEST,
    "aadhaar": ReasonCode.R11_AADHAAR_REQUEST,
    "pan": ReasonCode.R12_PAN_REQUEST,
    "bank account": ReasonCode.R13_BANK_DETAILS,
    "password": ReasonCode.R14_PASSWORD_REQUEST,
    
    # Threat keywords
    "arrest": ReasonCode.R20_ARREST_THREAT,
    "warrant": ReasonCode.R20_ARREST_THREAT,
    "jail": ReasonCode.R20_ARREST_THREAT,
    "legal action": ReasonCode.R21_LEGAL_ACTION,
    "account freeze": ReasonCode.R22_ACCOUNT_FREEZE,
    "police": ReasonCode.R23_POLICE_THREAT,
    
    # Urgency keywords
    "immediately": ReasonCode.R30_TIME_PRESSURE,
    "urgent": ReasonCode.R30_TIME_PRESSURE,
    "don't hang up": ReasonCode.R31_DONT_HANG_UP,
    "final warning": ReasonCode.R33_FINAL_WARNING,
    
    # Authority keywords
    "irs": ReasonCode.R40_GOVERNMENT_OFFICIAL,
    "bank": ReasonCode.R41_BANK_OFFICIAL,
    "police": ReasonCode.R42_POLICE_OFFICIAL,
    "microsoft": ReasonCode.R43_TECH_SUPPORT,
    
    # Scam phrases
    "compromised": ReasonCode.R50_ACCOUNT_COMPROMISED,
    "suspicious activity": ReasonCode.R51_SUSPICIOUS_ACTIVITY,
    "security alert": ReasonCode.R52_SECURITY_ALERT,
    "fraud alert": ReasonCode.R53_FRAUD_ALERT
}


def get_reason_codes_from_keywords(keywords: List[str]) -> List[str]:
    """Get reason codes based on detected keywords"""
    codes = set()
    for keyword in keywords:
        keyword_lower = keyword.lower()
        for kw, code in KEYWORD_TO_REASON_CODE.items():
            if kw in keyword_lower:
                codes.add(code.value)
    return list(codes)


def get_reason_codes_from_categories(categories: List[str]) -> List[str]:
    """Get reason codes based on detected categories"""
    codes = set()
    for category in categories:
        if category in CATEGORY_TO_REASON_CODES:
            for code in CATEGORY_TO_REASON_CODES[category]:
                codes.add(code.value)
    return list(codes)


def get_reason_explanation(code: str) -> str:
    """Get human-readable explanation for a reason code"""
    explanations = {
        "R01": "Cryptocurrency payment requested",
        "R02": "Gift card payment requested",
        "R03": "Wire transfer requested",
        "R04": "UPI payment requested",
        "R10": "OTP requested (DO NOT SHARE)",
        "R11": "Aadhaar number requested",
        "R12": "PAN number requested",
        "R20": "Arrest threat used",
        "R21": "Legal action threatened",
        "R22": "Account freeze threatened",
        "R30": "Urgency/Time pressure applied",
        "R31": "Told not to hang up",
        "R40": "Fake government official",
        "R41": "Fake bank official",
        "R50": "Claimed account compromised"
    }
    return explanations.get(code, f"Scam indicator: {code}")


class ReasonCodeGenerator:
    """Generate standardized reason codes for detection results"""
    
    def __init__(self):
        self.codes = []
    
    def generate(self, categories: List[str], keywords: List[str]) -> List[str]:
        """Generate reason codes from categories and keywords"""
        codes = set()
        
        # Add codes from categories
        codes.update(get_reason_codes_from_categories(categories))
        
        # Add codes from keywords
        codes.update(get_reason_codes_from_keywords(keywords))
        
        # Limit to top 5 most relevant
        return list(codes)[:5]
    
    def get_summary(self, codes: List[str]) -> str:
        """Get a human-readable summary of reason codes"""
        if not codes:
            return "No scam indicators"
        
        explanations = [get_reason_explanation(code) for code in codes]
        return "; ".join(explanations[:3])


if __name__ == "__main__":
    generator = ReasonCodeGenerator()
    
    # Test
    test_categories = ["payment_request", "urgency"]
    test_keywords = ["bitcoin", "immediately"]
    
    codes = generator.generate(test_categories, test_keywords)
    print(f"Categories: {test_categories}")
    print(f"Keywords: {test_keywords}")
    print(f"Reason Codes: {codes}")
    print(f"Summary: {generator.get_summary(codes)}")