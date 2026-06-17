"""
tracellm.storage — JSON file-based log storage with auto-rotation & stats aggregation.
"""

import os
import json
import time
import uuid
import shutil
from typing import Optional


DEFAULT_LOG_DIR = os.path.expanduser("~/.tracellm/logs")
MAX_ENTRIES_PER_FILE = 1000


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _resolve_log_dir(log_dir: Optional[str] = None) -> str:
    return log_dir if log_dir is not None else DEFAULT_LOG_DIR


def _log_file_path(log_dir: Optional[str] = None) -> str:
    resolved = _resolve_log_dir(log_dir)
    return os.path.join(_ensure_dir(resolved), "tracellm.jsonl")


def _archive_log(path: str) -> None:
    """Rotate log file: rename current → tracellm.jsonl.old, start fresh."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        archive = path + ".old"
        shutil.move(path, archive)


def write_log(
    entry: dict,
    log_dir: Optional[str] = None,
    max_entries: int = MAX_ENTRIES_PER_FILE,
) -> dict:
    """Append a log entry to the JSONL file; rotate if threshold reached."""
    entry.setdefault("id", str(uuid.uuid4()))
    entry.setdefault("timestamp", time.time())
    entry.setdefault("tokens", None)
    entry.setdefault("error", None)

    path = _log_file_path(log_dir)

    # Count current entries (rough check via line count)
    current_count = 0
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                for _ in f:
                    current_count += 1
        except Exception:
            current_count = 0

    if current_count >= max_entries:
        _archive_log(path)

    with open(path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def read_logs(log_dir: Optional[str] = None) -> list[dict]:
    """Read all log entries from the current log file."""
    path = _log_file_path(log_dir)
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def compute_stats(log_dir: Optional[str] = None) -> dict:
    """Aggregate statistics from current log file.

    Returns:
        total_calls, avg_latency (ms), error_rate (float 0-1),
        calls_by_model (dict[str, int]), calls_by_function (dict[str, int]).
    """
    logs = read_logs(log_dir)
    total = len(logs)
    if total == 0:
        return {
            "total_calls": 0,
            "avg_latency_ms": 0.0,
            "error_rate": 0.0,
            "calls_by_model": {},
            "calls_by_function": {},
        }

    latencies = [e.get("latency_ms", 0) or 0 for e in logs]
    errors = sum(1 for e in logs if not e.get("success", True))
    models: dict[str, int] = {}
    funcs: dict[str, int] = {}
    for e in logs:
        m = e.get("model", "unknown")
        models[m] = models.get(m, 0) + 1
        f = e.get("function_name", "unknown")
        funcs[f] = funcs.get(f, 0) + 1

    return {
        "total_calls": total,
        "avg_latency_ms": round(sum(latencies) / total, 2) if total else 0.0,
        "error_rate": round(errors / total, 4) if total else 0.0,
        "calls_by_model": models,
        "calls_by_function": funcs,
    }
