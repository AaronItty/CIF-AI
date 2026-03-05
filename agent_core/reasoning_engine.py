"""
Reasoning engine wrapper.
Interfaces with the LLM to extract intent and generate responses.

Now accepts dynamic tool descriptions from the Controller for prompt injection.
"""

import json
from groq import Groq
from typing import Dict, Any, List

class ReasoningEngine:
    """
    Wraps LLM calls for structured extraction and response generation.
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        # Using a fast reasoning model for intent extraction
        self.intent_model = "llama-3.1-8b-instant" 
        self.chat_model = "llama-3.1-8b-instant"
        
    async def extract_intent(self, text: str, context: List[Dict[str, Any]], tool_descriptions: str = "", user_context: dict = None) -> dict:
        """
        Extract user intent, entities, and requested actions from text.
        Forces the LLM to output a structured JSON response.
        
        tool_descriptions: A formatted string of available MCP tools, dynamically
                          discovered from the MCP server at runtime.
        user_context: Optional dict with known info about the user, e.g.
                     {"email": "user@example.com", "channel": "email"}
        """
        # Build tool instruction based on what's actually available
        if tool_descriptions and tool_descriptions != "No tools are currently available.":
            tool_instruction = (
                f"You have access to the following tools:\n{tool_descriptions}\n\n"
                "Decide intelligently whether to use a tool, ask for clarification, or respond directly. "
                "If you need more information from the user, be SPECIFIC about exactly what you need "
                "(e.g. 'What is your email address?' not 'Could you provide more details?'). "
                "If the user's intent matches a tool, set 'action' to the tool name and extract "
                "the relevant parameters into 'entities'. If no tool matches, set 'action' to 'none'."
            )
        else:
            tool_instruction = (
                "No tools are currently available. You must set 'action' to 'none' for all requests."
            )
        
        # Add user context if available
        user_context_str = ""
        if user_context:
            user_context_str = (
                "\nKnown information about the current user: "
                + ", ".join(f"{k}: {v}" for k, v in user_context.items())
                + ". Use this information when filling in tool parameters instead of using placeholder values like 'unknown'."
            )

        system_prompt = (
            "You are an intent extraction engine for a customer service AI agent. "
            "Analyze the user's input and determine what they want to do. "
            "Use your best judgement to decide whether to call a tool, ask for clarification, or respond directly. "
            "When asking for clarification, always specify exactly what information you need — never give vague responses. "
            f"{tool_instruction} "
            f"{user_context_str} "
            "You must respond in pure JSON format matching this schema: "
            '{"intent": "description of intent", "action": "tool_name_or_none", '
            '"entities": {"key": "value"}, "confidence": 0.0-1.0}'
        )
        
        # Build prompt messages including short context (last 10 messages)
        messages = [{"role": "system", "content": system_prompt}]
        
        print(f"\n--- [DEBUG] LLM Context Injection ---")
        print(f"Total raw history messages fetched: {len(context)}")
        print(f"Tools available: {'YES' if tool_descriptions else 'NO'}")
        
        # Filter context: Remove duplicates, keep recent messages
        # Deduplicate consecutive system messages (old repeated tool results)
        past_raw = [m for m in context if m.get("content") != text]
        deduplicated = []
        seen_system_contents = set()
        for msg in past_raw:
            content = msg.get("content", "")
            role = msg.get("role", "user")
            if role == "system":
                # Only keep unique system messages (tool results)
                content_key = content[:200]  # Use first 200 chars as key
                if content_key in seen_system_contents:
                    continue
                seen_system_contents.add(content_key)
            deduplicated.append(msg)
        
        past_messages = deduplicated[-6:]  # Keep last 6 unique messages
        print(f"Messages kept as history (excluding current): {len(past_messages)} (from {len(past_raw)} raw)")
        
        for msg in past_messages:
             role = msg.get("role", "user")
             content = msg.get("content", "")
             print(f"  - [{role}]: {content[:50]}...")
             messages.append({"role": role, "content": content})
             
        messages.append({"role": "user", "content": text})
        print(f"  - [CURRENT USER]: {text[:50]}...")
        print(f"------------------------------------\n")
        
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.intent_model,
            response_format={"type": "json_object"},
            temperature=0.0 # Deterministic extraction
        )
        
        result_content = response.choices[0].message.content
        return json.loads(result_content)
        
    async def generate_response(self, intent: dict, tool_results: dict, context: List[Dict[str, Any]] = None) -> str:
        """
        Generate a conversational response based on reasoning context and history.
        """
        system_prompt = (
            "You are a helpful, conversational AI agent. You have just completed an action on behalf of the user. "
            "Use the provided tool execution results, the original defined intent, and the conversation history to formulate a polite, human-readable response.\n\n"
            "IMPORTANT: If 'knowledge_base' content is provided in the tool results, you MUST base your answer primarily on that content. "
            "Quote or paraphrase the knowledge base information accurately. Do NOT make up information that isn't in the knowledge base. "
            "If the knowledge base has relevant info, use it to give a clear, helpful answer. "
            "If no knowledge base results are provided, answer conversationally based on what you know."
        )
        
        # Build message chain with history for the final conversational turn
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            # Add last 10 context messages for the final response generation
            for msg in context[-10:]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        user_prompt = f"Original Intent: {intent.get('intent')}\nTool Execution Results: {json.dumps(tool_results)}"
        messages.append({"role": "user", "content": user_prompt})
        
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.chat_model,
            temperature=0.5
        )
        
        return response.choices[0].message.content
