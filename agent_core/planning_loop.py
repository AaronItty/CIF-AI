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

    def _resolve_buy_item_ids(self, entities: dict, memory: list) -> dict:
        """
        Resolve human-readable store/product names to UUIDs by scanning
        past search_item results stored in conversation memory.
        """
        import re as _re
        
        uuid_pattern = _re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', _re.I)
        
        store_id = str(entities.get("store_id", "")).strip()
        product_id = str(entities.get("product_id", "")).strip()
        
        # If both are already UUIDs, nothing to do
        if uuid_pattern.match(store_id) and uuid_pattern.match(product_id):
            return entities
        
        # Scan memory for search_item results
        store_map = {}   # store_name.lower() -> store_id UUID
        product_map = {} # product_name.lower() -> product_id UUID
        
        for msg in memory:
            content = str(msg.get("content", ""))
            if "search_item" not in content or "results" not in content:
                continue
            
            # Try to extract the JSON from tool result
            try:
                import json as _json
                # Find the dict inside the message
                start = content.index("{")
                json_str = content[start:]
                data = _json.loads(json_str)
                
                results = data.get("results", [])
                for item in results:
                    s_id = item.get("store_id", "")
                    s_name = item.get("store_name", "")
                    p_id = item.get("product_id", "")
                    p_name = item.get("item_name", "") or item.get("product_name", "")
                    
                    if s_name and s_id:
                        store_map[s_name.lower()] = s_id
                    if p_name and p_id:
                        product_map[p_name.lower()] = p_id
            except (ValueError, _json.JSONDecodeError, Exception):
                continue
        
        # Resolve store_id
        if not uuid_pattern.match(store_id) and store_map:
            store_id_lower = store_id.lower()
            # Try exact match first, then partial match
            resolved = store_map.get(store_id_lower)
            if not resolved:
                for name, uid in store_map.items():
                    if store_id_lower in name or name in store_id_lower:
                        resolved = uid
                        break
            if resolved:
                print(f"[PlanningLoop] Resolved store_id: '{store_id}' -> '{resolved}'")
                entities["store_id"] = resolved
        
        # Resolve product_id
        if not uuid_pattern.match(product_id) and product_map:
            product_id_lower = product_id.lower()
            resolved = product_map.get(product_id_lower)
            if not resolved:
                for name, uid in product_map.items():
                    if product_id_lower in name or name in product_id_lower:
                        resolved = uid
                        break
            if resolved:
                print(f"[PlanningLoop] Resolved product_id: '{product_id}' -> '{resolved}'")
                entities["product_id"] = resolved
        
        return entities

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
                # For buy_item: validate required fields and confirm before executing
                if tool_name == "buy_item":
                    entities = intent.get("entities", {})
                    
                    # Resolve store_id and product_id from search results if they're names, not UUIDs
                    entities = self._resolve_buy_item_ids(entities, memory)
                    intent["entities"] = entities
                    
                    # Check for missing or placeholder values
                    required_fields = {
                        "customer_name": "your full name",
                        "customer_phone": "your phone number",
                        "customer_email": "your email address",
                        "pincode": "your delivery pincode"
                    }
                    missing = []
                    for field, label in required_fields.items():
                        val = str(entities.get(field, "")).strip()
                        if not val or val.lower() in ["unknown", "none", ""]:
                            missing.append(label)
                    
                    if missing:
                        # Ask for missing details instead of calling tool
                        missing_str = ", ".join(missing)
                        final_response_text = (
                            f"Before I can place this order, I still need the following: {missing_str}. "
                            "Could you please provide these details?"
                        )
                    else:
                        # Check if we already confirmed — look for a confirmation message
                        # in recent history that the user replied "yes" to
                        last_messages = memory[-4:] if len(memory) >= 4 else memory
                        already_confirmed = False
                        for msg in last_messages:
                            content = str(msg.get("content", ""))
                            if msg.get("role") == "assistant" and "confirm" in content.lower() and "order" in content.lower():
                                already_confirmed = True
                                break
                        
                        if not already_confirmed:
                            # Present order summary and ask for confirmation
                            product_name = entities.get("product_id", "the item")
                            qty = entities.get("quantity", 1)
                            addr = entities.get("delivery_address", "pickup")
                            pin = entities.get("pincode", "")
                            name = entities.get("customer_name", "")
                            phone = entities.get("customer_phone", "")
                            email = entities.get("customer_email", "")
                            
                            final_response_text = (
                                f"Please confirm the following order details:\n\n"
                                f"• **Name**: {name}\n"
                                f"• **Phone**: {phone}\n"
                                f"• **Email**: {email}\n"
                                f"• **Delivery Address**: {addr}\n"
                                f"• **Pincode**: {pin}\n"
                                f"• **Quantity**: {qty}\n\n"
                                "Reply **yes** to confirm and place the order, or let me know if anything needs to be changed."
                            )
                        else:
                            # User confirmed — actually place the order
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
                                    "I'm sorry, I'm having trouble placing the order right now. "
                                    "I am escalating to support."
                                )
                else:
                    # Other tools (search_item, escalate, etc.) — call directly
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
            # If the LLM wanted buy_item but confidence was low, 
            # run our validation to ask for specific missing fields
            intended_action = intent.get("action", "")
            if decision == "ask_clarification" and intended_action == "buy_item":
                entities = intent.get("entities", {})
                required_fields = {
                    "customer_name": "your full name",
                    "customer_phone": "your phone number",
                    "customer_email": "your email address",
                    "pincode": "your delivery pincode",
                    "delivery_address": "your delivery address"
                }
                missing = []
                for field, label in required_fields.items():
                    val = str(entities.get(field, "")).strip()
                    if not val or val.lower() in ["unknown", "none", ""]:
                        missing.append(label)
                
                if missing:
                    missing_str = ", ".join(missing)
                    final_response_text = (
                        f"I'd love to help you place that order! To proceed, I'll need: {missing_str}. "
                        "Could you please share these details?"
                    )
                else:
                    final_response_text = (
                        "I'd like to confirm your order details. Could you reply with 'yes' to place the order?"
                    )
            else:
                action_result = await self.controller.execute_action(
                    decision, intent,
                    session_id=session_id,
                    user_id=normalized_msg.user_id,
                    channel=normalized_msg.channel
                )
                final_response_text = action_result.get("message")
            
        elif decision == "respond":
            # Always check KB first before generating a direct response
            kb_context = await self._fetch_kb_context(normalized_msg.text)
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
            tags = [category] if (category and category != "one_of_the_labels_above") else None
            await self.state_manager.update_metadata(session_id, summary=summary, tags=tags)
        except Exception as e:
            print(f"[PlanningLoop] Metadata update failed: {e}")
            
        return {"response": final_response_text, "session_id": session_id}
