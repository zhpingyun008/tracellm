"""
tracellm.decorator — The @track_llm_call decorator for sync & async LLM calls.

Usage:

    from tracellm import track_llm_call

    @track_llm_call(model="gpt-4", max_retries=2)
    def call_openai(prompt: str) -> str:
        ...
"""

import asyncio
import functools
import time
import logging
from typing import Any, Callable, Optional, TypeVar

from tracellm.storage import write_log, compute_stats

logger = logging.getLogger("tracellm")

T = TypeVar("T")


def track_llm_call(
    model: str = "unknown",
    max_retries: int = 0,
    log_dir: Optional[str] = None,
    capture_tokens: bool = True,
):
    """Decorator that records LLM API call telemetry.

    Args:
        model: Model identifier to log (e.g. "gpt-4", "claude-3").
        max_retries: Number of retries on failure (capped at 3).
        log_dir: Custom log directory (default: ~/.tracellm/logs).
        capture_tokens: If True, tries to extract token info from
            the return value (looking for .usage.total_tokens or
            dict keys like 'total_tokens', 'input_tokens', 'output_tokens').
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return _run_call(
                func, args, kwargs, model, max_retries, log_dir, capture_tokens
            )

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await _run_call_async(
                func, args, kwargs, model, max_retries, log_dir, capture_tokens
            )

        wrapper = async_wrapper if is_async else sync_wrapper
        # Attach stats so users can call decorated_func.stats()
        wrapper.stats = lambda: compute_stats(log_dir or None)  # type: ignore
        return wrapper  # type: ignore

    return decorator


def _extract_tokens(result: Any) -> Optional[dict]:
    """Best-effort token usage extraction from common LLM response shapes."""
    if result is None:
        return None
    # Object with .usage.total_tokens (OpenAI / LiteLLM style)
    if hasattr(result, "usage") and hasattr(result.usage, "total_tokens"):
        usage = result.usage
        return {
            "total_tokens": getattr(usage, "total_tokens", None),
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
        }
    # Dict with nested 'usage' key
    if isinstance(result, dict):
        usage = result.get("usage") or result.get("usage_metadata")
        if isinstance(usage, dict):
            return {
                "total_tokens": usage.get("total_tokens") or usage.get("total_tokens"),
                "prompt_tokens": usage.get("prompt_tokens") or usage.get("input_tokens"),
                "completion_tokens": usage.get("completion_tokens") or usage.get("output_tokens"),
            }
        # Flat token keys
        if "total_tokens" in result:
            return {
                "total_tokens": result.get("total_tokens"),
                "prompt_tokens": result.get("prompt_tokens") or result.get("input_tokens"),
                "completion_tokens": result.get("completion_tokens") or result.get("output_tokens"),
            }
    return None


def _run_call(
    func: Callable,
    args: tuple,
    kwargs: dict,
    model: str,
    max_retries: int,
    log_dir: Optional[str],
    capture_tokens: bool,
) -> Any:
    last_error: Optional[str] = None
    start = time.time()

    for attempt in range(max(1, max_retries + 1)):
        try:
            result = func(*args, **kwargs)
            latency_ms = round((time.time() - start) * 1000, 2)

            tokens = _extract_tokens(result) if capture_tokens else None

            entry = {
                "model": model,
                "function_name": func.__name__,
                "latency_ms": latency_ms,
                "success": True,
                "error": None,
                "tokens": tokens,
                "attempt": attempt + 1,
            }
            write_log(entry, log_dir=log_dir)
            return result

        except Exception as e:
            last_error = str(e)
            logger.warning(
                "track_llm_call: attempt %d/%d failed for %s: %s",
                attempt + 1,
                max_retries + 1,
                func.__name__,
                last_error,
            )
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))  # simple backoff
                continue

            # All retries exhausted — log the error
            latency_ms = round((time.time() - start) * 1000, 2)
            entry = {
                "model": model,
                "function_name": func.__name__,
                "latency_ms": latency_ms,
                "success": False,
                "error": last_error,
                "tokens": None,
                "attempt": attempt + 1,
            }
            write_log(entry, log_dir=log_dir)
            raise


async def _run_call_async(
    func: Callable,
    args: tuple,
    kwargs: dict,
    model: str,
    max_retries: int,
    log_dir: Optional[str],
    capture_tokens: bool,
) -> Any:
    last_error: Optional[str] = None
    start = time.time()

    for attempt in range(max(1, max_retries + 1)):
        try:
            result = await func(*args, **kwargs)
            latency_ms = round((time.time() - start) * 1000, 2)

            tokens = _extract_tokens(result) if capture_tokens else None

            entry = {
                "model": model,
                "function_name": func.__name__,
                "latency_ms": latency_ms,
                "success": True,
                "error": None,
                "tokens": tokens,
                "attempt": attempt + 1,
            }
            write_log(entry, log_dir=log_dir)
            return result

        except Exception as e:
            last_error = str(e)
            logger.warning(
                "track_llm_call: attempt %d/%d failed for %s: %s",
                attempt + 1,
                max_retries + 1,
                func.__name__,
                last_error,
            )
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue

            latency_ms = round((time.time() - start) * 1000, 2)
            entry = {
                "model": model,
                "function_name": func.__name__,
                "latency_ms": latency_ms,
                "success": False,
                "error": last_error,
                "tokens": None,
                "attempt": attempt + 1,
            }
            write_log(entry, log_dir=log_dir)
            raise
