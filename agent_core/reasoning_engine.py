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
            "You must respond in pure JSON format matching this schema: "
            '{"intent": "description of intent", "action": "proposed_tool_name_or_none", '
            '"entities": {"key": "value"}, "confidence": 0.0-1.0}'
        )
        
        # Build prompt messages including short context (e.g. last 3 messages)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in context[-3:]:
             messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": text})
        
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.intent_model,
            response_format={"type": "json_object"},
            temperature=0.0 # Deterministic extraction
        )
        
        result_content = response.choices[0].message.content
        return json.loads(result_content)
        
    async def generate_response(self, intent: dict, tool_results: dict) -> str:
        """
        Generate a conversational response based on reasoning context.
        """
        system_prompt = (
            "You are a helpful, conversational AI agent. You have just completed an action on behalf of the user. "
            "Use the provided tool execution results and the original defined intent to formulate a polite, human-readable response."
        )
        
        user_prompt = f"Original Intent: {intent.get('intent')}\nTool Execution Results: {json.dumps(tool_results)}"
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.chat_model,
            temperature=0.5
        )
        
        return response.choices[0].message.content
