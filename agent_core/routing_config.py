"""
Routing configuration for handling escalations.
Maps conversation categories/tags to specific recipient email addresses.
"""

# Default recipient for all departments unless otherwise specified
DEFAULT_ESCALATION_EMAIL = "aaronittyipe670@gmail.com"

# Routing map: Category -> Recipient Email
ROUTING_MAP = {
    "Escalation": "aaronittyipe670@gmail.com",
    "Billing": "aaronittyipe670@gmail.com",
    "Technical Support": "aaronittyipe670@gmail.com",
    "Sales": "aaronittyipe670@gmail.com",
    "General Inquiry": "aaronittyipe670@gmail.com",
}

def get_recipient_for_category(category: str) -> str:
    """Returns the routed email address for a given category."""
    return ROUTING_MAP.get(category, DEFAULT_ESCALATION_EMAIL)
