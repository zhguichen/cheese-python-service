import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.logging import SessionLogContext, SessionLogger


def _load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_ensure_meta_creates_meta_line(tmp_path):
    logger = SessionLogger(tmp_path, "v1.0.0")
    context = SessionLogContext(user_id="u123", session_id="s456")

    meta_payload = {
        "session_id": "s456",
        "user_id": "u123",
        "book_name": "Python Basics",
        "book_introduction": "Prepared for new learners.",
        "section_id": "section-1",
        "section_content": "Sample content",
        "start_time": "2024-01-01T00:00:00+00:00",
    }

    logger.ensure_meta(context, meta_payload)

    log_file = tmp_path / "user_u123" / "session_s456.jsonl"
    assert log_file.exists()

    lines = _load_jsonl(log_file)
    assert len(lines) == 1
    assert lines[0]["meta"]["session_id"] == "s456"
    assert lines[0]["meta"]["version"] == "v1.0.0"
    assert lines[0]["meta"]["book_name"] == "Python Basics"


def test_append_event_appends_after_meta(tmp_path):
    logger = SessionLogger(tmp_path, "v1.0.0")
    context = SessionLogContext(user_id="u001", session_id="sess-1")

    logger.ensure_meta(
        context,
        {
            "session_id": "sess-1",
            "user_id": "u001",
            "book_name": "",
            "book_introduction": "",
            "section_id": "sec-1",
            "section_content": "",
            "start_time": "2024-01-01T00:00:00+00:00",
        },
    )

    logger.append_event(
        context,
        "generate",
        {"latency_ms": 123, "questions": []},
        timestamp="2024-01-01T00:01:00+00:00",
    )

    log_file = tmp_path / "user_u001" / "session_sess-1.jsonl"
    lines = _load_jsonl(log_file)
    assert len(lines) == 2
    assert lines[1]["event_type"] == "generate"
    assert lines[1]["timestamp"] == "2024-01-01T00:01:00+00:00"
    assert lines[1]["data"]["latency_ms"] == 123


def test_append_event_bootstraps_meta_when_missing(tmp_path):
    logger = SessionLogger(tmp_path, "v2.0.0")
    context = SessionLogContext(user_id="user-x", session_id="session-y")

    logger.append_event(
        context,
        "judge",
        {"latency_ms": 42, "results": []},
        timestamp="2024-02-02T00:00:00+00:00",
    )

    log_file = tmp_path / "user_user-x" / "session_session-y.jsonl"
    lines = _load_jsonl(log_file)
    assert len(lines) == 2

    meta = lines[0]["meta"]
    assert meta["session_id"] == "session-y"
    assert meta["user_id"] == "user-x"
    assert meta["version"] == "v2.0.0"
    # start_time should be a valid ISO timestamp
    datetime.fromisoformat(meta["start_time"])
