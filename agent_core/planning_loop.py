"""
Main planning loop.
Orchestrates the reason -> evaluate -> execute -> update cycle.
"""

import asyncio
from shared.interfaces import AgentInterface
from agent_core.reasoning_engine import ReasoningEngine
from agent_core.controller import Controller
from agent_core.state_manager import StateManager

class PlanningLoop(AgentInterface):
    """
    The orchestrator handling the while-not-resolved loop for the agent.
    """
    
    def __init__(self, reasoning: ReasoningEngine, controller: Controller, state_manager: StateManager):
        self.reasoning = reasoning
        self.controller = controller
        self.state_manager = state_manager
        
    async def process_message(self, user_id: str, session_id: str, message: str, channel: str) -> dict:
        """
        while not resolved:
            1. Extract intent
            2. Evaluate via controller
            3. Decide: respond / call tool / ask clarification / escalate
            4. Execute action
            5. Update memory
            6. Loop
        """
        resolved = False
        response = {}
        
        while not resolved:
            # Load memory
            memory = await self.state_manager.get_session_state(session_id)
            
            # Step 1: Extract Intent
            intent = await self.reasoning.extract_intent(message, memory)
            
            # Step 2 & 3: Evaluate & Decide
            decision = await self.controller.evaluate(intent, memory)
            
            # Step 4: Execute Action
            action_result = await self.controller.execute_action(decision, intent)
            
            # Update loop control
            if decision in ['respond', 'ask_clarification', 'escalate']:
                resolved = True
                response = action_result
            
            # Step 5: Update memory
            await self.state_manager.update_session_state(session_id, action_result)
            
        return response
