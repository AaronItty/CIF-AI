"""
Structured Controller.
The decision engine enforcing tool permissions, confidence thresholds,
escalation policies, and logic.
"""

from typing import Any, Dict
from agent_core.policy_engine import PolicyEngine

class Controller:
    """
    Evaluates extracted intents and strictly decides the next action.
    """
    
    def __init__(self, policy_engine: PolicyEngine, mcp_client: Any):
        self.policy_engine = policy_engine
        self.mcp_client = mcp_client
        
    async def evaluate(self, intent_data: Dict[str, Any], state: Dict[str, Any]) -> str:
        """
        Decide the next action based on policies and memory.
        Returns one of: 'respond', 'call_tool', 'ask_clarification', 'escalate'.
        """
        # 1. Check if we need to escalate based on explicit requests or state loops
        if self.policy_engine.should_escalate(state):
            return "escalate"
            
        action = intent_data.get("action")
        
        # 2. If no action (tool) is proposed by LLM, just chat/respond
        if not action or action == "none":
            # Just to be safe, if confidence is incredibly low even for a basic chat, ask to clarify
            if not self.policy_engine.evaluate_confidence(intent_data, threshold=0.5):
                return "ask_clarification"
            return "respond"
            
        # 3. If a tool is proposed, run strict policy checks
        # Check Confidence
        if not self.policy_engine.evaluate_confidence(intent_data, threshold=0.85):
            return "ask_clarification" # Or escalate, depending on design
            
        # Check Permissions
        user_role = state.get("user_role", "customer") # Default safely
        if not self.policy_engine.check_tool_permission(action, user_role):
            # Unauthorized action attempted
            return "escalate" 
            
        # Passed all checks -> safe to execute
        return "call_tool"
        
    async def execute_action(self, action_type: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the decided action (via MCP for tools, or formatting response).
        Logs all decisions made.
        """
        result = {"action_type": action_type}
        
        if action_type == "call_tool":
            tool_name = intent_data.get("action")
            tool_args = intent_data.get("entities", {})
            try:
                # Delegate entirely to the MCP client barrier
                # (Assuming mcp_client has a method `call_tool`)
                tool_output = await self.mcp_client.call_tool(tool_name, tool_args)
                result["tool_result"] = tool_output
                result["status"] = "success"
            except Exception as e:
                result["tool_result"] = f"Error executing {tool_name}: {str(e)}"
                result["status"] = "error"
                
        elif action_type == "ask_clarification":
            result["message"] = "I need a bit more clarification to confidently proceed. Could you provide more details?"
            
        elif action_type == "escalate":
            result["message"] = "I am transferring you to a human agent right away."
            # In real system, trigger backend handoff flag here
            
        elif action_type == "respond":
             # This will just proceed back to the Planning Loop which will call reasoning.generate_response
             result["status"] = "ready_to_respond"
             
        return result
