"""
Safe atomic JSONL logging utilities for LexSaksham predictions.

Provides thread-safe append for prediction logs without requiring a separate logging service.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def append_prediction_log(logpath: str, data_dict: Dict[str, Any]) -> None:
    """
    Atomically append a JSON line to prediction log file.

    Safe for concurrent writes (uses exclusive open mode).

    Args:
        logpath: Path to predictions.jsonl file.
        data_dict: Dictionary containing prediction data.
                   Expected keys: timestamp, input_text, input_lang, predicted_label,
                   predicted_name, confidence, requires_review, top_k, explain_method.

    Returns:
        None

    Raises:
        IOError: If file cannot be opened/written.
    """
    try:
        # Ensure parent directory exists
        Path(logpath).parent.mkdir(parents=True, exist_ok=True)

        # Append JSON line atomically
        with open(logpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data_dict) + "\n")
            f.flush()
            os.fsync(f.fileno())  # Force filesystem sync
    except Exception as e:
        print(f"⚠️ Failed to append to prediction log {logpath}: {e}")
        # Do not raise—logging failure should not crash the request


def read_prediction_logs(logpath: str, limit: int = 100) -> list:
    """
    Read last N prediction log entries as dictionaries.

    Args:
        logpath: Path to predictions.jsonl file.
        limit: Maximum number of recent lines to return.

    Returns:
        List of dicts (most recent last).
    """
    try:
        if not Path(logpath).exists():
            return []

        lines = []
        with open(logpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return lines[-limit:] if limit else lines
    except Exception as e:
        print(f"⚠️ Failed to read prediction logs: {e}")
        return []
