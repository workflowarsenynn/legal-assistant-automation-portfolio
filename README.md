# Legal Assistant Automation (Portfolio)

Portfolio-friendly Telegram intake bot for people dealing with debt or possible personal bankruptcy. The bot collects essential facts via a short finite-state dialogue, builds a concise summary, and stores the lead in SQLite (with a stub for Sheets/CRM). Optional LLM calls (OpenAI) classify the case and refine the summary; without an API key, the flow works in rule-based mode. Safe, anonymized code to showcase my automation skills.

## Features
- Telegram intake: guided, short dialogue for debt/bankruptcy inquiries.
- Explicit FSM: greeting → situation → debt details → city → documents → contacts → confirmation → close.
- SQLite storage: lightweight persistence with an initialization helper; stub for Sheets/CRM integration.
- Optional LLM: classification (type/urgency) and summary generation; safe fallback to rules.
- Layered design: transport (Telegram), domain/core (FSM orchestration, classification, summary), storage (SQLite), configuration/logging.
- Safe defaults: no secrets in code; environment-driven configuration with a provided `.env.example`.

## Architecture
- **src/config.py** — environment-driven settings (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `DB_PATH`, `LOG_LEVEL`).
- **src/logging_utils.py** — console/file logging with structured format.
- **src/bot/** — transport layer:
  - `telegram_client.py`: builds and runs the Telegram app.
  - `handlers.py`: routes `/start` and text updates to the intake flow.
  - `state_machine.py`: explicit FSM with limits on questions and graceful closure.
- **src/core/** — domain logic:
  - `intake_flow.py`: orchestrates FSM + classification + summary + persistence.
  - `legal_classification.py`: rule-based or OpenAI-driven classification.
  - `case_summary.py`: template or OpenAI-based summary builder.
  - `prompt_templates.py`: anonymized prompts for LLM usage.
- **src/storage/** — persistence:
  - `db.py`: SQLite schema + save helpers.
  - `sheets_client.py`: stub for Sheets/CRM-style integration (no external calls).
- **docs/architecture.md** — brief description of data flow and layering.

Data path: Telegram update → handlers → `IntakeFlow` → FSM → classification/summary → SQLite.

## Tech stack
- Python 3.11+
- [python-telegram-bot](https://python-telegram-bot.org/) v21.x
- SQLite (standard library)
- Optional: OpenAI API (via `openai` SDK)
- Utilities: `python-dotenv`, `logging`, `dataclasses`, `pytest` for tests

## How to run locally
1. Clone the repository.
2. Create `.env` from `.env.example` and fill `TELEGRAM_BOT_TOKEN`. Leave `OPENAI_API_KEY` empty to run in rule-based mode.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize and run the bot:
   ```bash
   python -m src.main
   ```
5. Interact in Telegram: `/start` → follow prompts. Without `OPENAI_API_KEY`, classification/summary fallback to deterministic rules.

## Production vs Portfolio
- **Production (not implemented here):** multi-channel intake (ads, other messengers), branching dialogues for services, lead scoring/prioritization, CRM/Sheets/BI integrations, anti-ban and platform-specific nuances.
- **Portfolio version (this repo):** focused Telegram intake for debt/bankruptcy, SQLite storage, optional LLM for classification/summary, clean layering to showcase FSM + (optional) LLM.

## Next steps / Improvements
- Integrate with CRM/Sheets for lead routing.
- Web dashboard to browse and annotate cases.
- Multi-channel transport adapters.
- CI/CD with automated tests and linting.
- Richer dialogue branches and service discovery flows.

## Testing
Run the lightweight tests (state machine and intake flow) locally:
```bash
pytest
```
