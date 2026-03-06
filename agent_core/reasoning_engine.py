"""
Reasoning engine wrapper.
Interfaces with the LLM to extract intent and generate responses.

Now accepts dynamic tool descriptions from the Controller for prompt injection.
"""

import json
from groq import AsyncGroq
from typing import Dict, Any, List

class ReasoningEngine:
    """
    Wraps LLM calls for structured extraction and response generation.
    """
    
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        # Using the latest powerhouse model (Llama 3.3 70B) for superior reasoning
        self.intent_model = "llama-3.3-70b-versatile" 
        self.chat_model = "llama-3.3-70b-versatile"
        
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
            past_summary = user_context.pop("past_context_summary", "No past context.")
            user_context_str = (
                "\n<PAST_CONTEXT_PROFILE>\n"
                f"{past_summary}\n"
                "</PAST_CONTEXT_PROFILE>\n\n"
                "Known information about the current user (Use this instead of placeholders like 'unknown'):\n"
                + ", ".join(f"{k}: {v}" for k, v in user_context.items())
            )

        system_prompt = (
            "You are an intent extraction engine for a customer service AI agent. "
            "Extract user intent, entities, and requested actions from text. "
            "Follow this Reasoning Hierarchy for every query:\n"
            "1. TOOL CALL: If the user action matching an MCP tool, PRIORITIZE the tool. "
            "2. CLARIFY: If the request is vague or missing required parameters, ask for clarification. "
            "3. CONTEXT CHECK: If you need to recall something from the past that isn't in your <PAST_CONTEXT_PROFILE>, use the 'get_conversation_history' tool. "
            "4. RESPONSE/KB: If no tool is needed, provide a helpful direct response. (Your system will automatically inject background knowledge if you choose to respond).\n\n"
            f"{tool_instruction} "
            f"{user_context_str} "
            "\nCRITICAL INSTRUCTION: Treat the <PAST_CONTEXT_PROFILE> merely as background background info. "
            "Recent messages in the history are much more important than older ones. "
            "ONLY extract the intent and tool actions for the CURRENT User message. Do not hallucinate tools failing right now just because they failed in the past context. "
            "If the user is frustrated, identifies as 'tired of talking to a bot', mentions 'useless', or explicitly asks to speak to a human, "
            "SET action to 'escalate_to_human' with HIGH confidence (1.0). "
            "IMPORTANT: Categorize the conversation into one of these labels: 'Technical Support', 'Billing', 'Sales', 'General Inquiry', 'Escalation'. "
            "You must respond in pure JSON format matching this schema: "
            '{"intent": "description of intent", "category": "one_of_the_labels_above", "action": "tool_name_or_none", '
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
             
        print(f"  - [CURRENT USER]: {text[:50]}...", flush=True)
        print(f"------------------------------------\n", flush=True)
        
        try:
            print(f"[REASONING] Sending request to Groq model {self.intent_model}...", flush=True)
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.intent_model,
                response_format={"type": "json_object"},
                temperature=0.0 # Deterministic extraction
            )
            print(f"[REASONING] Groq request complete.", flush=True)
        except Exception as e:
            print(f"[REASONING] FATAL GROQ ERROR: {e}", flush=True)
            raise e
        
        result_content = response.choices[0].message.content
        return json.loads(result_content)
        
    async def generate_response(self, intent: dict, tool_results: dict, context: List[Dict[str, Any]] = None) -> str:
        """
        Generate a conversational response based on reasoning context and history.
        """
        system_prompt = (
            "You are a helpful, conversational AI agent. You have just completed an action on behalf of the user. "
            "Use the provided tool execution results, the original defined intent, and the conversation history to formulate a polite, human-readable response.\n\n"
            "CLEANLINESS RULES:\n"
            "1. NEVER show technical internal IDs (like UUIDs for products or stores) to the user. Use the human names instead.\n"
            "2. Do not explain technical details (like 'calling MCP tool') — just provide the result.\n"
            "3. Avoid using JSON-like structures in your speech. Speak naturally.\n\n"
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
        
        try:
            print(f"[REASONING] Generating final response with {self.chat_model}...", flush=True)
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.chat_model,
                temperature=0.5
            )
            print(f"[REASONING] Final response received.", flush=True)
        except Exception as e:
            print(f"[REASONING] GROQ GENERATION ERROR: {e}", flush=True)
            raise e
        
        return response.choices[0].message.content

    async def summarize_conversation(self, context: List[Dict[str, Any]]) -> str:
        """Generate a one-sentence summary of the conversation history."""
        if not context:
            return ""
            
        system_prompt = (
            "Summarize the following conversation in one short, clear sentence. "
            "Focus on the user's primary goal or issue. Do not use 'The user wants...' or 'This conversation is about...'. "
            "Example: 'Inquiry regarding billing error on February invoice.'"
        )
        
        # Build message chain for summarization
        messages = [{"role": "system", "content": system_prompt}]
        for msg in context[-15:]:  # Use last 15 messages for summary
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        try:
            print(f"[REASONING] Summarizing conversation history...", flush=True)
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.chat_model,
                temperature=0.3, # More focused/stable for summaries
                max_tokens=60
            )
            print(f"[REASONING] Summary generation complete.", flush=True)
        except Exception as e:
            print(f"[REASONING] SUMMARIZATION ERROR: {e}", flush=True)
            return "Conversation in progress" # Fail gracefully for summary

        return response.choices[0].message.content.strip()

    async def summarize_detailed_context(self, context: List[Dict[str, Any]]) -> str:
        """Generate a detailed context profile focusing on intent and user entities."""
        if not context:
            return "No previous context."
            
        system_prompt = (
            "You are a context preservation engine. Your job is to read the preceding conversation "
            "and output a dense, structured Context Profile that summarizes everything that has happened so far.\n"
            "You MUST extract and retain any specific details provided by the user, such as:\n"
            "- Full Name\n"
            "- Email Address\n"
            "- Phone Number\n"
            "- Mailing or Physical Address\n"
            "- Product Names or Order IDs\n\n"
            "Format your output clearly. For example:\n"
            "Intent: User is inquiring about store policies.\n"
            "Entities Known: Name: John Doe, Email: john@example.com.\n"
            "Do NOT include conversational filler."
        )
        
        # Build message chain for summarization
        messages = [{"role": "system", "content": system_prompt}]
        for msg in context[-20:]:  # Use last 20 messages for deep context
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        try:
            print(f"[REASONING] Generating Detailed Context Profile...", flush=True)
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.chat_model,
                temperature=0.1, # Highly deterministic for fact extraction
                max_tokens=250
            )
            print(f"[REASONING] Detailed Profile generation complete.", flush=True)
        except Exception as e:
            print(f"[REASONING] DETAILED SUMMARIZATION ERROR: {e}", flush=True)
            return "Context in progress. Some data may have been lost."
            
        return response.choices[0].message.content.strip()
