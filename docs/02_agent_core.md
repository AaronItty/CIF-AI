# 02 - Agent Core Layer

## Subsystem Overview
The Agent Core acts as the cognitive engine for the platform. It wraps LLM reasoning within a highly deterministic and structured Controller loop.

## Ownership & Boundaries
- **Owned by:** Agent Core Team
- **Boundary:** The Core dictates logic but does NOT execute external side-effects directly. To touch a backend service, it delegates securely to the **MCP Server**. Memory state is offloaded to the **Dashboard/Supabase** layer.

## Architecture

### Planning Loop
The heart of the AI process runs continuously until the user's intent is fully resolved during that turn.
```python
while not resolved:
    1. Extract intent
    2. Evaluate via controller
    3. Decide: respond / call tool / ask clarification / escalate
    4. Execute action
    5. Update memory
    6. Loop
```

### Components
1. **ReasoningEngine (`reasoning_engine.py`):** Wraps LLM API calls. Does intent extraction. Does not decide what tool to run on its own; it proposes an intent.
2. **Controller (`controller.py`):** The deterministic router. Uses the `PolicyEngine` to grant/deny the ReasoningEngine's proposed tool use.
3. **PolicyEngine (`policy_engine.py`):** Controls autonomy limits. E.g., if LLM confidence < 0.85, force `ask_clarification` or `escalate`.

## Flow Diagram
```text
[Communication Layer]
        |
        v
[PlanningLoop]
  ├─> (1) StateManager: load context
  ├─> (2) ReasoningEngine: extract intent ("I want a refund")
  ├─> (3) Controller + PolicyEngine: Validate tool permissions
  |       - "refund_tool" allowed? Yes. Confidence > 0.9? Yes.
  ├─> (4) Controller requests MCP Server: execute("process_refund")
  ├─> (5) StateManager: log tool result
  └─> (6) Loop again -> Re-evaluate context -> Decide: respond("Refund processed")
        |
        v
[Communication Layer]
```

## Autonomy & Escalation Triggers
- **Low Confidence:** The LLM's raw intent probability falls below configured thresholds.
- **Fail Loop:** A tool fails 3 times consecutively (caught by Controller state).
- **Explicit Request:** User strictly states "Talk to human".
When triggered, `PolicyEngine` returns 'escalate', prompting the `Controller` to hand off via `EscalationRouter`.

## Future Extensibility Notes
- The Planning Loop can be migrated to frameworks like LangGraph or AutoGen if multi-agent capabilities become necessary, but the deterministic Controller constraint must remain.

## TODOs
- [ ] Refine LLM prompt engineering for Intent extraction.
- [ ] Integrate actual MCP execution paths.
- [ ] Finalize confidence scoring heuristics.
