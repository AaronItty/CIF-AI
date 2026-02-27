# 01 - Communication Layer

## Subsystem Overview
The Communication Layer is responsible for handling all incoming and outgoing messages across various channels (Telegram, Email, Voice). It ensures that the Agent Core operates on normalized, channel-agnostic data structures.

## Ownership & Boundaries
- **Owned by:** Communications Team
- **Boundary:** Stateless. Must contain zero business logic or decision-making processes. It acts purely as a conduit between the end-user and the Agent Core.

## Interfaces
- **Inputs:** Raw platform-specific payloads (e.g., Telegram Updates, IMAP Email content, Voice Transcripts).
- **Outputs:** Standardized dictionaries or dataclasses passing user intent and session data to the `AgentInterface.process_message()`.
- **Expected Return from Core:** Standardized responses to be mapped back to channel-specific payloads.

## Integration Plan
1. `channel_manager.py` loops over registered channels and runs their listeners asynchronously.
2. Handlers (`telegram_handler.py`, `email_handler.py`) parse and normalize data.
3. Handlers call `agent.process_message(...)`.
4. If `escalation_router.py` is invoked by the core, the channel pauses AI handling and routes raw input directly to the human UI.

## Flow Diagram
```text
[User Telegram] -> (Webhook/Poll)
                       |
                       v
            [TelegramHandler._handle_incoming]
                       | -> Normalizes format to {user_id, session_id, message}
                       v
             [AgentCore.PlanningLoop]
                       | -> Processes intent & context
                       v
             (Returns standard response)
                       |
                       v
            [TelegramHandler.send_message]
                       |
                       v
                 [User Telegram]
```

## Escalation Routing
When the core signals an escalation, the `EscalationRouter` takes over the session state in Supabase, assigning it to a human. The Communication layer then routes subsequent messages to the human interface rather than the Agent Core until resolved.

## Future Extensibility Notes
- Easy to add `whatsapp_handler.py` or fully implement `call_handler.py` with Twilio.
- Normalization schema can be expanded into formal Pydantic models.

## TODOs
- [ ] Implement actual webhooks for Telegram (currently stubbed).
- [ ] Set up IMAP/SMTP details for Email integration.
- [ ] Flesh out Twilio wrapper for Voice integration.
