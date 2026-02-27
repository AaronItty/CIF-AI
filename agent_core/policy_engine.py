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
            "customer": ["get_order_status", "faq_search"],
            "admin": ["get_order_status", "faq_search", "process_refund", "update_database"]
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
        Evaluate context against escalation triggers (e.g., repeating failed loops, explicit user requests).
        """
        # Example check 1: Explicit user request to talk to human
        user_message = state.get("latest_user_message", "").lower()
        if any(trigger in user_message for trigger in ["human", "agent", "support", "escalate", "help"]):
            return True
            
        # Example check 2: Too many repeated tool failures
        failures = state.get("consecutive_tool_failures", 0)
        if failures >= 3:
            return True
            
        return False
