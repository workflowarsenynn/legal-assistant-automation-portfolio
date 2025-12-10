import sqlite3
from pathlib import Path

from src.core.intake_flow import IntakeFlow
from src.storage.db import init_db


def test_intake_flow_saves_case():
    db_path = Path("data/test_cases.db")
    if db_path.exists():
        db_path.unlink()
    init_db(str(db_path))

    flow = IntakeFlow(openai_api_key=None, db_path=str(db_path))

    result = flow.start_session("chat-42")
    assert result.state.name == "CASE_DESCRIPTION"

    flow.process_message("chat-42", "I have an overdue credit card loan")
    flow.process_message("chat-42", "Credit card and consumer loan")
    flow.process_message("chat-42", "Metropolis")
    flow.process_message("chat-42", "Court letter available")
    flow.process_message("chat-42", "Jordan Doe, +123456789")

    final = flow.process_message("chat-42", "yes")
    assert final.saved is True

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    assert count == 1
