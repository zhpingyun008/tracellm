"""
tracellm — Lightweight LLM API call tracking with a simple decorator.

Track latency, tokens, errors, and model usage for any LLM call.
"""

from tracellm.decorator import track_llm_call
from tracellm.storage import compute_stats, read_logs, write_log

__version__ = "0.1.0"
__all__ = ["track_llm_call", "compute_stats", "read_logs", "write_log"]
