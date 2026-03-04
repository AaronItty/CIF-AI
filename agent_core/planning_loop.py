"""
Main planning loop.
Orchestrates the reason -> evaluate -> execute -> update cycle.

Now triggers MCP tool discovery at startup and passes tool info to the ReasoningEngine.
"""

import asyncio
from typing import Dict, Any

# Assuming these exist in a shared directory based on original imports
# class AgentInterface: pass
# from shared.interfaces import AgentInterface
# For now, avoiding missing imports by removing AgentInterface inheritance if not strictly required
# Or keeping it as a dummy if needed. I will remove AgentInterface inheritance to ensure it runs standalone.

from agent_core.reasoning_engine import ReasoningEngine
from agent_core.controller import Controller
from agent_core.state_manager import StateManager
from communication.schemas.normalized_message import NormalizedMessage

class PlanningLoop:
    """
    The orchestrator handling the while-not-resolved loop for the agent.
    """
    
    def __init__(self, reasoning: ReasoningEngine, controller: Controller, state_manager: StateManager):
        self.reasoning = reasoning
        self.controller = controller
        self.state_manager = state_manager
        self._tools_discovered = False
        
    async def _ensure_tools_discovered(self):
        """Discover MCP tools once, then cache for subsequent requests."""
        if not self._tools_discovered:
            await self.controller.discover_tools()
            self._tools_discovered = True
        
    async def _call_tool_with_retries(self, decision, intent, normalized_msg, session_id, max_retries=3):
        """Call a tool with retries. Returns (tool_name, tool_result_or_None, action_result)."""
        tool_name = intent.get("action")
        tool_args = intent.get("entities", {})
        tool_result = None
        action_result = {}
        
        for attempt in range(1, max_retries + 1):
            print(f"[PlanningLoop] Tool call attempt {attempt}/{max_retries} for '{tool_name}'")
            action_result = await self.controller.execute_action(
                decision, intent,
                session_id=session_id,
                user_id=normalized_msg.user_id,
                channel=normalized_msg.channel
            )
            
            if action_result.get("status") == "success":
                tool_result = action_result.get("tool_result")
                print(f"[PlanningLoop] Tool '{tool_name}' succeeded on attempt {attempt}")
                break
            else:
                print(f"[PlanningLoop] Tool '{tool_name}' failed on attempt {attempt}: {action_result.get('tool_result')}")
        
        # Log and save to memory
        await self.state_manager.log_tool_usage(session_id, tool_name, tool_args, action_result)
        await self.state_manager.update_session_state(session_id, {
            "role": "system",
            "content": f"Tool '{tool_name}' returned: {tool_result or action_result.get('tool_result')}"
        })
        
        return tool_name, tool_result, action_result

    async def process_message(self, normalized_msg: NormalizedMessage) -> dict:
        """
        Flow:
            1. Discover tools (once)
            2. Extract intent (once per message)
            3. Evaluate via controller
            4. Execute action
            5. If history tool → inject context, re-extract intent, call next tool
            6. If other tool succeeded → generate response immediately
            7. If tool failed → retry up to 3x
            8. If no tool needed → respond or clarify
        """
        session_id = normalized_msg.session_id
        message = normalized_msg.message
        
        # Ensure tools are discovered from MCP server
        await self._ensure_tools_discovered()
        
        # Get the dynamic tool descriptions for the LLM prompt
        tool_descriptions = self.controller.get_tool_descriptions_for_prompt()
        
        # Save the new incoming user message to memory immediately
        await self.state_manager.update_session_state(session_id, {
            "role": "user",
            "content": message,
            "channel": normalized_msg.channel,
            "user_id": normalized_msg.user_id
        })
        
        final_response_text = ""
        
        # Extract user email from user_id (format: "Name <email>" or just "email")
        import re
        user_id = normalized_msg.user_id
        email_match = re.search(r'<(.+?)>', user_id)
        user_email = email_match.group(1) if email_match else user_id
        user_context = {
            "email": user_email,
            "channel": normalized_msg.channel
        }
        
        # Step 1: Load memory
        memory = await self.state_manager.get_session_state(session_id)
        print(f"[DEBUG] PlanningLoop: Loaded {len(memory)} messages from memory for session {session_id}")
        
        # Create a simplified state dict for the Policy Engine evaluation
        eval_state = {
            "user_role": "admin",
            "latest_user_message": message,
            "consecutive_tool_failures": 0
        }
        
        # Step 2: Extract Intent ONCE using Groq (with dynamic tool descriptions)
        intent = await self.reasoning.extract_intent(message, memory, tool_descriptions, user_context=user_context)
        original_intent = intent
        
        # Step 3: Evaluate & Decide using strict deterministic Controller
        decision = await self.controller.evaluate(intent, eval_state)
        
        # Step 4: Execute based on decision
        if decision == "call_tool":
            tool_name = intent.get("action")
            accumulated_tool_results = {}
            
            # Special handling: if the agent wants conversation history first,
            # fetch it, then re-extract intent for a follow-up action
            if tool_name == "get_conversation_history":
                print("[PlanningLoop] Agent requested conversation history — fetching context first")
                _, hist_result, _ = await self._call_tool_with_retries(
                    decision, intent, normalized_msg, session_id
                )
                
                if hist_result is not None:
                    accumulated_tool_results["get_conversation_history"] = hist_result
                    
                    # Re-extract intent now that context is richer
                    memory = await self.state_manager.get_session_state(session_id)
                    intent = await self.reasoning.extract_intent(message, memory, tool_descriptions, user_context=user_context)
                    decision = await self.controller.evaluate(intent, eval_state)
                    tool_name = intent.get("action")
                    
                    # If the agent now wants another tool, call it
                    if decision == "call_tool" and tool_name != "get_conversation_history":
                        _, tool_result, _ = await self._call_tool_with_retries(
                            decision, intent, normalized_msg, session_id
                        )
                        if tool_result is not None:
                            accumulated_tool_results[tool_name] = tool_result
                
                # Generate response with all accumulated results
                memory = await self.state_manager.get_session_state(session_id)
                final_response_text = await self.reasoning.generate_response(
                    original_intent, accumulated_tool_results, memory
                )
            else:
                # Normal tool call (search_item, buy_item, escalate, etc.)
                _, tool_result, _ = await self._call_tool_with_retries(
                    decision, intent, normalized_msg, session_id
                )
                
                if tool_result is not None:
                    accumulated_tool_results[tool_name] = tool_result
                    memory = await self.state_manager.get_session_state(session_id)
                    final_response_text = await self.reasoning.generate_response(
                        original_intent, accumulated_tool_results, memory
                    )
                else:
                    final_response_text = (
                        "I'm sorry, I'm having trouble completing this request right now. "
                        "I am escalating to support."
                    )
                
        elif decision in ["ask_clarification", "escalate"]:
            action_result = await self.controller.execute_action(
                decision, intent,
                session_id=session_id,
                user_id=normalized_msg.user_id,
                channel=normalized_msg.channel
            )
            final_response_text = action_result.get("message")
            
        elif decision == "respond":
            # No tool needed — generate a conversational reply
            final_response_text = await self.reasoning.generate_response(
                original_intent, {}, memory
            )
             
        # Save the final AI response to memory
        await self.state_manager.update_session_state(session_id, {
            "role": "assistant",
            "content": final_response_text
        })
            
        return {"response": final_response_text, "session_id": session_id}
