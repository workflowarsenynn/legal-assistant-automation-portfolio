"""Stub interface for sending cases to Google Sheets or other CRMs."""
from __future__ import annotations

import logging
from typing import Optional

from src.core.case_summary import IntakeData

logger = logging.getLogger(__name__)


class SheetsClient:
    """Placeholder client showing how a spreadsheet integration could look."""

    def __init__(self, credentials_path: Optional[str] = None) -> None:
        self.credentials_path = credentials_path

    def append_case(self, intake_data: IntakeData) -> None:
        """Stub method for appending a case to a spreadsheet-like store."""

        logger.info(
            "SheetsClient.append_case called for name=%s (stub, no external call)", intake_data.client_name
        )
        # In production, this method would authenticate and push data to Sheets/CRM.
        return None
