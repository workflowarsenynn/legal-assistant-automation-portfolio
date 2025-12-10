# Architecture

## Overview
The project uses a layered approach to keep transport, domain, and storage concerns separate. Telegram is the only transport in this portfolio version; all sensitive configuration lives in environment variables.

## Layers
- **bot**: Telegram wiring (`telegram_client.py`), handler registration, and the explicit finite-state machine (`state_machine.py`). The FSM enforces step order, caps clarifying attempts, and gracefully closes when limits are reached.
- **core**: Domain orchestration in `intake_flow.py`, which combines the FSM with classification (`legal_classification.py`), summary generation (`case_summary.py`), and prompt templates. Classification and summary support both rule-based and optional OpenAI flows.
- **storage**: SQLite helpers in `db.py` to initialize the schema and persist confirmed cases; `sheets_client.py` illustrates how a spreadsheet/CRM adapter could look.
- **config & logging**: Environment-driven configuration (`config.py`) and structured logging (`logging_utils.py`).

## Data flow
1. Telegram update arrives → `handlers.py` resolves chat ID and forwards to `IntakeFlow`.
2. `IntakeFlow` delegates to `IntakeStateMachine` to decide the next prompt and collect context.
3. On confirmation, `IntakeFlow` optionally classifies the case, builds a summary, and persists the lead via SQLite.
4. Errors are logged; limits trigger a polite close with whatever data is available.

## Extensibility notes
- Transport adapters can be added alongside the Telegram client without touching domain logic.
- Storage can be swapped by implementing the same `save_case` contract (e.g., CRM, Sheets, BI pipelines).
- Prompts are anonymized and can be extended without leaking production rules.
