# Harmful words ki list
BLOCKED_KEYWORDS = [
    "bomb", "kill", "hack", "password", "credit card",
    "suicide", "drugs", "weapon"
]

def check_query(query: str) -> dict:
    """
    Query check karta hai — safe hai ya nahi
    Returns: dict with allowed=True/False and reason
    """
    
    # Query ko lowercase mein convert karo
    # Taaki "BOMB" aur "bomb" dono pakad sake
    query_lower = query.lower()
    
    # Har blocked keyword check karo
    for keyword in BLOCKED_KEYWORDS:
        if keyword in query_lower:
            return {
                "allowed": False,
                "reason": f"I can't help with that. Please ask something appropriate."
            }
    
    # Agar sab theek hai
    return {
        "allowed": True,
        "reason": None
    }