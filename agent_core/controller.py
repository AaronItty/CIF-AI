"""
Structured Controller.
The decision engine enforcing tool permissions, confidence thresholds,
escalation policies, and logic.

Now uses the FastMCP Client for dynamic tool discovery and execution.
"""

import json
from typing import Any, Dict, List
from agent_core.policy_engine import PolicyEngine

class Controller:
    """
    Evaluates extracted intents and strictly decides the next action.
    Connects to the MCP server to discover and execute tools.
    """
    
    def __init__(self, policy_engine: PolicyEngine, mcp_server_url: str, mcp_shared_secret: str):
        self.policy_engine = policy_engine
        self.mcp_url = mcp_server_url
        self.mcp_secret = mcp_shared_secret
        self._available_tools: List[dict] = []
        
    async def discover_tools(self) -> List[dict]:
        """
        Connect to the MCP server and retrieve available tool schemas.
        Returns a list of tool dicts with name, description, and inputSchema.
        """
        if not self.mcp_url:
            print("[Controller] No MCP_SERVER_URL configured. Tool calling disabled.")
            return []
            
        try:
            from fastmcp import Client
            async with Client(self.mcp_url) as client:
                tools = await client.list_tools()
                self._available_tools = [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema
                    }
                    for t in tools
                ]
                print(f"[Controller] Discovered {len(self._available_tools)} tools from MCP server:")
                for t in self._available_tools:
                    print(f"  - {t['name']}: {t['description'][:60]}...")
                return self._available_tools
        except Exception as e:
            print(f"[Controller] Failed to discover tools from MCP server: {e}")
            return []

    def get_tool_descriptions_for_prompt(self) -> str:
        """
        Format discovered tools into a string the LLM can use in its system prompt.
        """
        if not self._available_tools:
            return "No tools are currently available."
        
        lines = []
        for tool in self._available_tools:
            schema = tool.get("input_schema", {})
            props = schema.get("properties", {})
            required = schema.get("required", [])
            
            params = []
            for param_name, param_info in props.items():
                param_type = param_info.get("type", "string")
                req_marker = " (required)" if param_name in required else " (optional)"
                params.append(f"    - {param_name}: {param_type}{req_marker}")
            
            param_str = "\n".join(params) if params else "    (no parameters)"
            lines.append(f"- {tool['name']}: {tool['description']}\n  Parameters:\n{param_str}")
        
        return "\n".join(lines)
        
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
        if not action or action == "none" or not self.mcp_url:
            if not action or action == "none":
                # Just to be safe, if confidence is incredibly low even for a basic chat, ask to clarify
                if not self.policy_engine.evaluate_confidence(intent_data, threshold=0.5):
                    return "ask_clarification"
            return "respond"
            
        # 3. If a tool is proposed, run strict policy checks
        # Check Confidence
        if not self.policy_engine.evaluate_confidence(intent_data, threshold=0.85):
            return "ask_clarification"
            
        # Check Permissions
        user_role = state.get("user_role", "customer")
        if not self.policy_engine.check_tool_permission(action, user_role):
            return "escalate" 
            
        # Passed all checks -> safe to execute
        return "call_tool"
        
    async def execute_action(self, action_type: str, intent_data: Dict[str, Any], **context) -> Dict[str, Any]:
        """
        Execute the decided action.
        Uses the FastMCP Client to call tools on the MCP server.
        
        context kwargs may include: session_id, user_id, channel
        """
        result = {"action_type": action_type}
        
        if action_type == "call_tool":
            tool_name = intent_data.get("action")
            tool_args = intent_data.get("entities", {})
            try:
                from fastmcp import Client
                
                async with Client(self.mcp_url) as client:
                    tool_result = await client.call_tool(tool_name, tool_args)
                    
                    # tool_result is a list of content blocks; extract text
                    result_text = ""
                    for block in tool_result:
                        if hasattr(block, 'text'):
                            result_text += block.text
                    
                    # Try to parse as JSON for structured output
                    try:
                        result["tool_result"] = json.loads(result_text)
                    except (json.JSONDecodeError, TypeError):
                        result["tool_result"] = result_text
                        
                result["status"] = "success"
            except Exception as e:
                result["tool_result"] = f"Error executing {tool_name}: {str(e)}"
                result["status"] = "error"
                
        elif action_type == "ask_clarification":
            result["message"] = "I need a bit more clarification to confidently proceed. Could you provide more details?"
            
        elif action_type == "escalate":
            # Auto-escalation triggered by PolicyEngine (e.g., 3 consecutive failures).
            # We call the MCP escalate_to_human tool so the DB is updated and email is sent.
            session_id = context.get("session_id", "unknown")
            user_contact = context.get("user_id", "unknown")
            channel = context.get("channel", "unknown")
            
            try:
                from fastmcp import Client
                
                async with Client(self.mcp_url) as client:
                    tool_result = await client.call_tool("escalate_to_human", {
                        "session_id": session_id,
                        "reason": "Automatic escalation: repeated tool failures or policy trigger.",
                        "user_contact": user_contact,
                        "channel": channel
                    })
                    print(f"[Controller] Auto-escalation MCP result: {tool_result}")
            except Exception as e:
                print(f"[Controller] Auto-escalation MCP call failed: {e}")
            
            result["message"] = "I am transferring you to a human agent right away. A support team member will follow up shortly."
            
        elif action_type == "respond":
             result["status"] = "ready_to_respond"
             
        return result
