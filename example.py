#!/usr/bin/env python3
"""
tracellm — Example usage demonstrating the @track_llm_call decorator.

Tests sync, async, error handling, and stats aggregation.
"""

import os
import sys
import time
import json
import shutil

# Ensure we can import tracellm from the local source
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tracellm import track_llm_call, compute_stats, read_logs


# Clear any previous logs so results are deterministic
DEFAULT_LOG_DIR = os.path.expanduser("~/.tracellm/logs")
if os.path.exists(DEFAULT_LOG_DIR):
    shutil.rmtree(DEFAULT_LOG_DIR)


# ── Mock AI functions ─────────────────────────────────────────────────────────

@track_llm_call(model="gpt-4", max_retries=1)
def mock_openai_call(prompt: str, simulate_error: bool = False) -> str:
    """Simulate an OpenAI API call."""
    time.sleep(0.05)  # simulate network latency
    if simulate_error:
        raise RuntimeError("API rate limit exceeded")
    return f"Response to: {prompt[:30]}..."


@track_llm_call(model="claude-3-opus", max_retries=0)
def mock_claude_call(prompt: str) -> dict:
    """Simulate a Claude API call returning token usage."""
    time.sleep(0.03)
    return {
        "content": f"Claude response to: {prompt[:20]}...",
        "usage": {
            "input_tokens": 25,
            "output_tokens": 80,
            "total_tokens": 105,
        },
    }


@track_llm_call(model="gpt-4-turbo")
async def mock_async_call(prompt: str) -> str:
    """Simulate an async API call."""
    import asyncio
    await asyncio.sleep(0.04)
    return f"Async response: {prompt[:20]}..."


@track_llm_call(model="always-fails", max_retries=2)
def mock_failure_call(prompt: str) -> str:
    """Function that always fails to test error tracking."""
    time.sleep(0.01)
    raise ConnectionError("Unable to reach LLM API endpoint")


# ── Main test ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  tracellm — LLM Call Tracker Demo")
    print("=" * 60)

    print(f"\nLog directory: {DEFAULT_LOG_DIR}")

    # ── 1. Sync calls ──────────────────────────────────────────────────────
    print("\n─── Sync calls ───")
    r1 = mock_openai_call("What is the capital of France?")
    print(f"  gpt-4 result: {r1}")

    r2 = mock_openai_call("Explain quantum computing simply.")
    print(f"  gpt-4 result: {r2}")

    r3 = mock_claude_call("Write a haiku about Python.")
    if isinstance(r3, dict):
        print(f"  claude result: {r3.get('content', r3)}")

    # ── 2. Async call ──────────────────────────────────────────────────────
    print("\n─── Async call ───")
    import asyncio
    r4 = asyncio.run(mock_async_call("Hello from async world!"))
    print(f"  async result: {r4}")

    # ── 3. Error call (with retries) ───────────────────────────────────────
    print("\n─── Error call (with retries) ───")
    try:
        mock_failure_call("This will fail.")
    except ConnectionError as e:
        print(f"  Caught expected error: {e}")

    # ── 4. Stats verification ──────────────────────────────────────────────
    print("\n─── Stats ───")
    stats = compute_stats()
    print(f"  Total calls:     {stats['total_calls']}")
    print(f"  Avg latency:     {stats['avg_latency_ms']} ms")
    print(f"  Error rate:      {stats['error_rate']:.2%}")
    print(f"  Calls by model:  {json.dumps(stats['calls_by_model'], indent=4)}")
    print(f"  Calls by function: {json.dumps(stats['calls_by_function'], indent=4)}")

    # ── 5. Raw logs ────────────────────────────────────────────────────────
    print("\n─── Raw logs (all entries) ───")
    logs = read_logs()
    for i, entry in enumerate(logs):
        print(f"  [{i+1}] {entry.get('function_name')} | "
              f"model={entry.get('model')} | "
              f"latency={entry.get('latency_ms')}ms | "
              f"success={entry.get('success')} | "
              f"error={entry.get('error')}")

    if logs:
        last = logs[-1]
        if last.get("tokens"):
            print(f"\n  Token details (from claude call): {last['tokens']}")

    print("\n─── Validation ───")
    assert stats["total_calls"] == 5, f"Expected 5, got {stats['total_calls']}"
    assert stats["calls_by_model"]["gpt-4"] == 2
    assert stats["calls_by_model"]["claude-3-opus"] == 1
    assert stats["calls_by_model"]["gpt-4-turbo"] == 1
    assert stats["calls_by_model"]["always-fails"] == 1
    assert stats["error_rate"] > 0, "Expected at least one error"
    print("  ✅ All assertions passed!")
    print("\n" + "=" * 60)
    print("  tracellm demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
