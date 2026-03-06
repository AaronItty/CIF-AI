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
from agent_core.routing_config import get_recipient_for_category

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
                # Reset failure counter on success
                await self.state_manager.update_session_meta(session_id, "consecutive_tool_failures", 0)
                break
            else:
                print(f"[PlanningLoop] Tool '{tool_name}' failed on attempt {attempt}: {action_result.get('tool_result')}")
                # Increment failure counter
                current_failures = await self.state_manager.get_session_meta(session_id, "consecutive_tool_failures", 0)
                await self.state_manager.update_session_meta(session_id, "consecutive_tool_failures", current_failures + 1)
        
        # Log and save to memory
        await self.state_manager.log_tool_usage(session_id, tool_name, tool_args, action_result)
        await self.state_manager.update_session_state(session_id, {
            "role": "system",
            "content": f"Tool '{tool_name}' returned: {tool_result or action_result.get('tool_result')}"
        })
        
        return tool_name, tool_result, action_result



    async def _fetch_kb_context(self, query_text: str) -> str:
        """
        Query the knowledge base via MCP tool and return relevant content.
        Returns formatted KB context string, or None if no results.
        """
        try:
            from fastmcp import Client
            async with Client(self.controller.mcp_url) as client:
                result = await client.call_tool("query_knowledge_base", {"query": query_text})
                
                result_text = ""
                for block in (result.content if hasattr(result, 'content') else result):
                    if hasattr(block, 'text'):
                        result_text += block.text
                
                import json
                data = json.loads(result_text)
                results = data.get("results", [])
                
                if not results:
                    return None
                
                # Format KB content for injection
                kb_parts = []
                for i, r in enumerate(results, 1):
                    content = r.get("content", "")
                    sim = r.get("similarity", 0)
                    kb_parts.append(f"[KB #{i} (relevance: {sim})] {content}")
                
                kb_context = "\n\n".join(kb_parts)
                print(f"[PlanningLoop] KB context fetched: {len(results)} entries")
                return kb_context
                
        except Exception as e:
            print(f"[PlanningLoop] KB fetch failed (non-critical): {e}")
            return None

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
        accumulated_tool_results = {}
        print("[DEBUG] PlanningLoop: accumulated_tool_results initialized", flush=True)
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
        
        # Reset the consecutive failure counter for every new message to avoid "failure deadlock"
        # from previous conversations. The 3-strike rule will now apply per-request.
        await self.state_manager.update_session_meta(session_id, "consecutive_tool_failures", 0)
        
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
        # Load failure counter from session metadata
        consecutive_failures = await self.state_manager.get_session_meta(session_id, "consecutive_tool_failures", 0)
        eval_state = {
            "user_role": "admin",
            "latest_user_message": message,
            "consecutive_tool_failures": consecutive_failures
        }
        
        # Generate the Detailed Context Summary to prevent LLM hallucination of old tool runs
        detailed_context_summary = await self.reasoning.summarize_detailed_context(memory)
        user_context["past_context_summary"] = detailed_context_summary

        # Prepare the turn memory. 
        # If the user message is very short (e.g., "Yes", "No", "Confirm"), 
        # we include the last turn (User+AI) so the Intent Extractor knows the context of the confirmation.
        is_sparse = len(message.strip()) < 15 or message.strip().lower() in ["yes", "no", "confirm", "sure", "ok", "that's it"]
        if is_sparse and len(memory) >= 2:
            current_turn_memory = memory[-2:] + [{"role": "user", "content": message}]
        else:
            current_turn_memory = [{"role": "user", "content": message}]

        # Step 2: Extract Intent ONCE using Groq (with dynamic tool descriptions)
        intent = await self.reasoning.extract_intent(message, current_turn_memory, tool_descriptions, user_context=user_context)
        original_intent = intent
        
        # Step 3: Evaluate & Decide using strict deterministic Controller
        decision = await self.controller.evaluate(intent, eval_state)
        
        # --- [AUTO-ESCALATION SAFETY CHECK] ---
        # If the category suggests escalation but the LLM didn't choose the tool, force it.
        category = intent.get("category")
        action = intent.get("action")
        
        # We trigger auto-escalation ONLY for the "Escalation" category if handled poorly by LLM.
        # Routing tags like "Billing" or "Technical Support" will route if an escalation happens,
        # but they won't FORCE one.
        routing_tags = ["Escalation"] 
        if category in routing_tags and action != "escalate_to_human" and decision != "escalate":
            print(f"[PlanningLoop] AUTO-ESCALATE: Category '{category}' detected but action was '{action}'. Forcing escalation.")
            decision = "escalate"
            intent["action"] = "escalate_to_human"
            intent["entities"] = {"reason": f"Category '{category}' identified — transferring to support."}
        
        # Enrich intent with routed recipient email if it's an escalation
        if intent.get("action") == "escalate_to_human":
            recipient = get_recipient_for_category(category)
            if "entities" not in intent:
                intent["entities"] = {}
            intent["entities"]["recipient_email"] = recipient
            print(f"[PlanningLoop] Routing escalation to: {recipient}")

        # Step 4: Execute based on decision
        if decision == "call_tool":
            tool_name = intent.get("action")
            
            # Enrich with KB context proactively for tool-based responses
            # (e.g. searching for an item might need shipping policy info)
            kb_context = await self._fetch_kb_context(message)
            if kb_context:
                accumulated_tool_results["knowledge_base"] = kb_context
            
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
                
                # Enrich with KB context before final generation
                kb_context = await self._fetch_kb_context(message)
                if kb_context:
                    accumulated_tool_results["knowledge_base"] = kb_context

                # Generate response with all accumulated results
                memory = await self.state_manager.get_session_state(session_id)
                final_response_text = await self.reasoning.generate_response(
                    original_intent, accumulated_tool_results, memory
                )
            else:
                # EXECUTE any other tool directly (search_item, escalate_to_human, etc.)
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
                
        elif decision == "ask_clarification":
            # If the LLM wanted buy_item but confidence was low, 
            # run our validation to ask for specific missing fields
            # Fallback to general clarification
            action_result = await self.controller.execute_action(
                decision, intent,
                session_id=session_id,
                user_id=normalized_msg.user_id,
                channel=normalized_msg.channel
            )
            final_response_text = action_result.get("message")
                
        elif decision == "escalate":
            # Just execute the escalation action, no buy_item validation
            action_result = await self.controller.execute_action(
                decision, intent,
                session_id=session_id,
                user_id=normalized_msg.user_id,
                channel=normalized_msg.channel
            )
            final_response_text = action_result.get("message")
            
        elif decision == "respond":
            # Always check KB first before generating a direct response
            kb_context = await self._fetch_kb_context(normalized_msg.message)
            if kb_context:
                accumulated_tool_results["knowledge_base"] = kb_context
            final_response_text = await self.reasoning.generate_response(
                original_intent, accumulated_tool_results, memory
            )
             
        # Save the final AI response to memory
        await self.state_manager.update_session_state(session_id, {
            "role": "assistant",
            "content": final_response_text
        })
        
        # Step 6: Generate Summary and Persist Metadata
        try:
            # Refresh memory to include the latest turn
            updated_memory = await self.state_manager.get_session_state(session_id)
            summary = await self.reasoning.summarize_conversation(updated_memory)
            
            # Persist summary and tags
            category = intent.get("category")
            tags = [category] if (category and category != "one_of_the_labels_above") else None
            await self.state_manager.update_metadata(session_id, summary=summary, tags=tags)
        except Exception as e:
            print(f"[PlanningLoop] Metadata update failed: {e}")
            
        return {"response": final_response_text, "session_id": session_id, "metadata": normalized_msg.metadata}
