"""
Prepared demo transcripts for Defend & Detect: Real-Time Scam Call Shield
Each scenario is designed to showcase the linguistic agent's capabilities.
"""

TEST_SCRIPTS = {
    "ai_style_bank": """
Caller: Hello, this is an automated message from your bank's security department.
We have detected suspicious activity on your account. To prevent your account from being frozen, please press 1 to speak with a representative immediately. This is urgent.
""",
    "human_style_bank": """
Caller: Hello sir, main bank se bol raha hoon. Aapka account mein problem hai.
Aap jaldi se apna OTP batao. Nahi toh account band ho jayega. Jaldi karo.
"""
}

DEMO_SCENARIOS = {
    "safe_amazon_call": {
        "name": "Safe Call: Amazon Refund",
        "transcript": """
Caller: Hi, this is Priya from Amazon customer service. I'm calling about your recent return.
Victim: Oh yes, the book I returned.
Caller: Just confirming the refund has been processed. You should see it in 3-5 days. No action needed from you.
Victim: Thank you so much!
Caller: You're welcome. Have a great day!
""",
        "expected_risk": "SAFE",
        "description": "Normal customer service call - should NOT trigger any alert"
    },
    
    "bank_kyc_scam": {
        "name": "Scam: Bank KYC Impersonation",
        "transcript": """
Caller: Hello, this is Rajesh from State Bank of India. Your KYC is pending update.
Victim: Oh, I thought I completed it.
Caller: No sir, it's showing incomplete. Your account will be blocked in 2 hours if not updated.
Caller: To avoid this, please download AnyDesk app and share the OTP you receive. This is very urgent.
""",
        "expected_risk": "DANGEROUS",
        "description": "Classic bank impersonation with urgency and OTP request"
    },
    
    "hinglish_police_scam": {
        "name": "Scam: Hinglish Police Impersonation",
        "transcript": """
Caller: Hello, main Inspector Sharma bol raha hoon, Delhi Police Cyber Cell se.
Victim: Ji, boliye.
Caller: Aapke Aadhaar card ka galat istemal hua hai. Money laundering case mein naam aaya hai.
Caller: Turant verify karna hoga. Aapna account number aur IFSC code batao, nahi toh arrest warrant nikalega.
Victim: Par maine toh kuch nahi kiya!
Caller: Jaldi karo, time nahi hai. OTP bhi aayega, woh bhi batao.
""",
        "expected_risk": "DANGEROUS",
        "description": "Hinglish police impersonation with threats and data requests"
    },
    
    "courier_scam": {
        "name": "Scam: Fake Courier Customs",
        "transcript": """
Caller: This is FedEx customs department. A package in your name contains illegal items.
Victim: What? I didn't order anything illegal!
Caller: The package is flagged. Press 1 to speak with a customs officer immediately.
Caller: To avoid legal action, you must pay a customs clearance fee of ₹4,999 via Google Pay right now.
Victim: This must be a mistake...
Caller: Sir, the police will be informed if you don't comply. Pay now.
""",
        "expected_risk": "DANGEROUS",
        "description": "Courier scam with payment pressure and threats"
    },
    
    "escalating_tech_support": {
        "name": "Scam: Escalating Tech Support (Streaming)",
        "chunks": [
            ("Caller", "Hello, I'm calling from Microsoft Windows support."),
            ("Caller", "We've detected a virus on your computer."),
            ("Caller", "Your personal data is at risk. I need to secure your device immediately."),
            ("Caller", "Please download TeamViewer so I can fix it."),
            ("Caller", "Also, for verification, read me the OTP you'll receive."),
        ],
        "expected_risk": "DANGEROUS",
        "description": "Tech support scam that escalates over time - tests real-time chunk analysis"
    },
    
    "normal_family_call": {
        "name": "Safe Call: Family Conversation",
        "transcript": """
Caller: Hey beta, khana khaya?
Victim: Haan mummy, bas abhi khatam kiya.
Caller: Theek hai. Shaam ko ghar aa rahe ho?
Victim: Haan, 7 baje tak pahunch jaunga.
Caller: Achha, sambhal ke aana.
""",
        "expected_risk": "SAFE",
        "description": "Normal family call in Hindi - should be safe"
    }
}