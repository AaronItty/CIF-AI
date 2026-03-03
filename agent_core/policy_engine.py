"""
Policy Engine module.
Enforces autonomy boundaries, tool permissions, and escalation triggers.
"""

from typing import Dict, Any

class PolicyEngine:
    """
    Defines the boundaries of what the Agent is allowed to do autonomously.
    """
    
    def __init__(self):
        # Example RBAC mapping: {role: [allowed_tools]}
        # In a real app, this might come from Supabase or Auth0
        self.role_permissions = {
            "customer": ["search_item", "escalate_to_human", "get_order_status", "faq_search"],
            "admin": ["search_item", "buy_item", "escalate_to_human", "get_order_status", "faq_search", "update_database"]
        }
        
    def check_tool_permission(self, tool_name: str, role: str) -> bool:
        """
        Validate whether the given role is allowed to invoke the tool.
        """
        if role == "admin":
             return True # Admins can do everything locally for now
        allowed_tools = self.role_permissions.get(role, [])
        return tool_name in allowed_tools
        
    def evaluate_confidence(self, intent: Dict[str, Any], threshold: float = 0.85) -> bool:
        """
        Determine if the LLM's intent confidence clears the autonomous threshold.
        """
        confidence = intent.get("confidence", 0.0)
        return confidence >= threshold
        
    def should_escalate(self, state: Dict[str, Any]) -> bool:
        """
        Evaluate context against escalation triggers.
        Only triggers on consecutive tool failures (3+).
        Keyword-based triggers have been removed to avoid false positives.
        """
        # Check: Too many repeated tool failures
        failures = state.get("consecutive_tool_failures", 0)
        if failures >= 3:
            return True
            
        return False
