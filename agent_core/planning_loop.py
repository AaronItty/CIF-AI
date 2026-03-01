"""
Main planning loop.
Orchestrates the reason -> evaluate -> execute -> update cycle.
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
        
    async def process_message(self, normalized_msg: NormalizedMessage) -> dict:
        """
        while not resolved:
            1. Extract intent
            2. Evaluate via controller
            3. Decide: respond / call tool / ask clarification / escalate
            4. Execute action
            5. Update memory
            6. Loop
        """
        session_id = normalized_msg.session_id
        message = normalized_msg.message
        
        # Save the new incoming user message to memory immediately
        await self.state_manager.update_session_state(session_id, {
            "role": "user",
            "content": message,
            "channel": normalized_msg.channel,
            "user_id": normalized_msg.user_id
        })
        
        resolved = False
        final_response_text = ""
        
        # We might accumulate tool results if the LLM calls multiple tools in succession
        accumulated_tool_results = {}
        original_intent = {}

        # Failsafe loop counter to prevent infinite loops
        loops = 0
        MAX_LOOPS = 5
        
        while not resolved and loops < MAX_LOOPS:
            loops += 1
            
            # Step 1: Load memory
            memory = await self.state_manager.get_session_state(session_id)
            print(f"[DEBUG] PlanningLoop: Loaded {len(memory)} messages from memory for session {session_id}")
            
            # Create a simplified state dict for the Policy Engine evaluation
            # (e.g., getting user_role from db, checking consecutive failures, etc)
            eval_state = {
                "user_role": "admin", # Hardcoded for now, would fetch from DB based on user_id
                "latest_user_message": message,
                "consecutive_tool_failures": 0 # Would compute from memory in a real app
            }
            
            # Step 2: Extract Intent using Groq
            intent = await self.reasoning.extract_intent(message, memory)
            if loops == 1:
                 # Save the original intent for the final conversational response
                 original_intent = intent
            
            # Step 3: Evaluate & Decide using strict deterministic Controller
            decision = await self.controller.evaluate(intent, eval_state)
            
            # Step 4: Execute Action (run tool via MCP or format standard response)
            action_result = await self.controller.execute_action(decision, intent)
            
            # Step 5: Update loop control & memory
            if decision == "call_tool":
                # A tool was executed. Log it and loop again to let the LLM see the result!
                tool_name = intent.get("action")
                await self.state_manager.log_tool_usage(
                    session_id, 
                    tool_name, 
                    intent.get("entities", {}), 
                    action_result
                )
                # Save tool output as a "system" or "tool" message so Groq can read it next loop
                await self.state_manager.update_session_state(session_id, {
                    "role": "system",
                    "content": f"Tool '{tool_name}' returned: {action_result.get('tool_result')}"
                })
                # Store accumulated results for final response generation
                accumulated_tool_results[tool_name] = action_result.get('tool_result')
                
            elif decision in ["ask_clarification", "escalate"]:
                # Controller decided to stop and ask the user a question or handoff
                resolved = True
                final_response_text = action_result.get("message")
                
            elif decision == "respond":
                # Controller says we have all info. We use Groq to generate a final conversational reply
                resolved = True
                final_response_text = await self.reasoning.generate_response(original_intent, accumulated_tool_results, memory)
                
        # Failsafe breach
        if not resolved:
             final_response_text = "I'm sorry, I'm having trouble completing this request right now. I am escalating to support."
             
        # Save the final AI response to memory
        await self.state_manager.update_session_state(session_id, {
            "role": "assistant",
            "content": final_response_text
        })
            
        return {"response": final_response_text, "session_id": session_id}
