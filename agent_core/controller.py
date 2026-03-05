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
        
        Confidence thresholds:
          >= 0.85 → call_tool (proceed)
          0.75–0.85 → ask_clarification (detail what was understood)
          < 0.75 → escalate to human
        """
        # 1. Check if we need to escalate based on consecutive failures
        if self.policy_engine.should_escalate(state):
            return "escalate"
            
        action = intent_data.get("action")
        confidence = intent_data.get("confidence", 0.0)
        
        # 2. If no action (tool) is proposed by LLM, just chat/respond
        if not action or action == "none" or not self.mcp_url:
            if not action or action == "none":
                if confidence < 0.5:
                    return "escalate"
            return "respond"
            
        # 3. If a tool is proposed, run confidence checks
        if confidence < 0.75:
            return "escalate"
        
        if confidence < 0.85:
            return "ask_clarification"
            
        # 4. Check Permissions
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
            
            # Inject runtime context for tools that need it
            if tool_name == "escalate_to_human":
                if "session_id" not in tool_args and "session_id" in context:
                    tool_args["session_id"] = context["session_id"]
                if "user_contact" not in tool_args and "user_id" in context:
                    tool_args["user_contact"] = context["user_id"]
                if "channel" not in tool_args and "channel" in context:
                    tool_args["channel"] = context["channel"]
            
            # Auto-inject for other tools if they happen to need session_id
            if "session_id" in context and "session_id" not in tool_args:
                tool_args["session_id"] = context["session_id"]
            
            # Validate required args before calling the tool
            tool_schema = next((t for t in self._available_tools if t["name"] == tool_name), None)
            if tool_schema:
                schema = tool_schema.get("input_schema", {})
                required_params = schema.get("required", [])
                missing_params = [p for p in required_params if p not in tool_args or not tool_args[p]]
                if missing_params:
                    print(f"[Controller] Tool '{tool_name}' missing required args: {missing_params}")
                    result["tool_result"] = f"Cannot call {tool_name}: missing required parameters: {', '.join(missing_params)}"
                    result["status"] = "error"
                    return result
            
            print(f"[Controller] Calling tool '{tool_name}' with args: {tool_args}")
            try:
                from fastmcp import Client
                
                async with Client(self.mcp_url) as client:
                    tool_result = await client.call_tool(tool_name, tool_args)
                    
                    # tool_result is a CallToolResult; access .content for blocks
                    result_text = ""
                    content_blocks = tool_result.content if hasattr(tool_result, 'content') else tool_result
                    for block in content_blocks:
                        if hasattr(block, 'text'):
                            result_text += block.text
                    
                    # Try to parse as JSON for structured output
                    try:
                        result["tool_result"] = json.loads(result_text)
                    except (json.JSONDecodeError, TypeError):
                        result["tool_result"] = result_text
                        
                result["status"] = "success"
                print(f"[Controller] Tool '{tool_name}' returned successfully")
            except Exception as e:
                print(f"[Controller] Tool '{tool_name}' FAILED: {e}")
                result["tool_result"] = f"Error executing {tool_name}: {str(e)}"
                result["status"] = "error"
                
        elif action_type == "ask_clarification":
            # Show what the agent understood and ask for confirmation
            intent_desc = intent_data.get("intent", "")
            action_name = intent_data.get("action", "")
            entities = intent_data.get("entities", {})
            
            # Build a detailed "this is what I understood" message
            parts = []
            if intent_desc:
                parts.append(f"Here's what I understood from your message: **{intent_desc}**")
            if action_name and action_name != "none":
                parts.append(f"I was planning to use the **{action_name}** tool")
            if entities:
                detail_items = [f"  • {k}: {v}" for k, v in entities.items() if v]
                if detail_items:
                    parts.append("With these details:\n" + "\n".join(detail_items))
            
            if parts:
                summary = "\n\n".join(parts)
                result["message"] = (
                    f"{summary}\n\n"
                    "Is this what you're looking for, or did you mean something else? "
                    "Please clarify so I can help you better."
                )
            else:
                result["message"] = (
                    "I'm not quite sure what you need. Could you rephrase your request? "
                    "For example, are you looking to search for a product, place an order, "
                    "or ask about a policy?"
                )
            
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
