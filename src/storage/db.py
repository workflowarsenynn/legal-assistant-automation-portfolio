"""SQLite storage layer for intake cases."""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.case_summary import IntakeData

logger = logging.getLogger(__name__)


def init_db(db_path: str) -> None:
    """Create required tables if they do not exist."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                chat_id TEXT,
                name TEXT,
                city TEXT,
                debt_type TEXT,
                urgency TEXT,
                debt_details TEXT,
                docs_info TEXT,
                case_summary TEXT,
                contact_info TEXT,
                status TEXT,
                notes TEXT
            )
            """
        )
    logger.info("SQLite initialized at %s", path)


def save_case(db_path: str, chat_id: str, intake: IntakeData, summary_text: Optional[str] = None) -> int:
    """Persist a confirmed case into the SQLite database."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    created_at = datetime.utcnow().isoformat()

    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cases (
                created_at,
                chat_id,
                name,
                city,
                debt_type,
                urgency,
                debt_details,
                docs_info,
                case_summary,
                contact_info,
                status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                chat_id,
                intake.client_name,
                intake.city,
                intake.classification.type if intake.classification else None,
                intake.classification.urgency if intake.classification else None,
                intake.debt_details,
                intake.docs_info,
                summary_text,
                intake.contact_info,
                "new",
                intake.notes,
            ),
        )
        conn.commit()
        case_id = cursor.lastrowid
    logger.info("Saved case %s for chat %s", case_id, chat_id)
    return case_id
