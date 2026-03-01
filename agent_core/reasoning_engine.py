"""
Reasoning engine wrapper.
Interfaces with the LLM to extract intent and generate responses.
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
        
    async def extract_intent(self, text: str, context: List[Dict[str, Any]]) -> dict:
        """
        Extract user intent, entities, and requested actions from text.
        Forces the LLM to output a structured JSON response.
        """
        system_prompt = (
            "You are an intent extraction engine. Analyze the user's input and determine what they want to do. "
            "IMPORTANT: Tools and Actions are currently OFFLINE. You must set 'action' to 'none' for all requests. "
            "You must respond in pure JSON format matching this schema: "
            '{"intent": "description of intent", "action": "none", '
            '"entities": {"key": "value"}, "confidence": 0.0-1.0}'
        )
        
        # Build prompt messages including short context (last 10 messages)
        # We limit to the most recent 10 to stay within the user's requested 'memory' limit.
        messages = [{"role": "system", "content": system_prompt}]
        
        print(f"\n--- [DEBUG] LLM Context Injection ---")
        print(f"Total raw history messages fetched: {len(context)}")
        
        # Filter context: Keep only past messages (exclude the one we just saved if it's already in there)
        # We also limit to the most recent 10.
        past_messages = [m for m in context if m.get("content") != text][-10:]
        print(f"Messages kept as history (excluding current): {len(past_messages)}")
        
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
            "Use the provided tool execution results, the original defined intent, and the conversation history to formulate a polite, human-readable response."
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
