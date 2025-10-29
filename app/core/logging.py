"""
Session logging utilities for AI practice workflows.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_timestamp() -> str:
    """Return current timestamp in ISO 8601 format with timezone info."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SessionLogContext:
    """Basic context identifiers for a session log."""

    user_id: str
    session_id: str


class SessionLogger:
    """Manage JSONL session logs according to the logging specification."""

    def __init__(self, base_dir: Path, version: str) -> None:
        self._base_dir = base_dir
        self._version = version

    def _session_file(self, context: SessionLogContext) -> Path:
        """Calculate the session log path for a user and session."""
        return (
            self._base_dir
            / f"user_{context.user_id}"
            / f"session_{context.session_id}.jsonl"
        )

    def ensure_meta(self, context: SessionLogContext, meta: Dict[str, Any]) -> None:
        """
        Ensure the session meta line exists.

        If the log file does not exist, create directories and write the meta line.
        """
        session_file = self._session_file(context)
        if session_file.exists():
            return

        session_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"meta": self._build_meta(meta)}

        with session_file.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def append_event(
        self,
        context: SessionLogContext,
        event_type: str,
        data: Dict[str, Any],
        *,
        timestamp: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append an event row to the session log, creating the file if required.

        Args:
            context: Session identifiers.
            event_type: Event type string (generate, answer, judge).
            data: Event payload.
            timestamp: Optional ISO timestamp. Defaults to current time.
            meta: Optional meta payload used when the session file has not been initialised.
        """
        session_file = self._session_file(context)
        if not session_file.exists():
            fallback_meta = meta or self._default_meta(context)
            self.ensure_meta(context, fallback_meta)

        event_payload = {
            "event_type": event_type,
            "timestamp": timestamp or _utc_timestamp(),
            "data": data,
        }

        with session_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event_payload, ensure_ascii=False) + "\n")

    def _build_meta(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Merge default metadata with the supplied payload."""
        merged = {
            "session_id": meta.get("session_id", ""),
            "user_id": meta.get("user_id", ""),
            "book_name": meta.get("book_name", ""),
            "book_introduction": meta.get("book_introduction", ""),
            "section_id": meta.get("section_id", ""),
            "section_content": meta.get("section_content", ""),
            "start_time": meta.get("start_time", _utc_timestamp()),
            "version": meta.get("version", self._version),
        }
        return merged

    def _default_meta(self, context: SessionLogContext) -> Dict[str, Any]:
        """Build a minimal meta payload when no extra information is available."""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "book_name": "",
            "book_introduction": "",
            "section_id": "",
            "section_content": "",
            "start_time": _utc_timestamp(),
            "version": self._version,
        }
