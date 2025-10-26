"""Structured logging utilities with context propagation."""
from __future__ import annotations

import logging
import os
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, get_contextvars

__all__ = [
    "bind_context",
    "bind_trace",
    "clear_trace",
    "configure_logging",
    "get_logger",
    "get_trace_id",
]

_TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)
_CONFIGURED = False


def _resolve_level(level: str | int | None) -> int:
    if level is None:
        level = os.getenv("LOUSA_LOG_LEVEL", "INFO")
    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)
    return int(level)


def configure_logging(level: str | int | None = None, force: bool = False) -> None:
    """Configure structlog with JSON output and distributed trace support."""

    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    resolved_level = _resolve_level(level)
    logging.basicConfig(level=resolved_level, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        cache_logger_on_first_use=True,
    )

    clear_contextvars()
    _TRACE_ID.set(None)
    _CONFIGURED = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a configured structlog logger."""

    configure_logging()
    return structlog.get_logger(name)


def bind_trace(trace_id: str | None = None) -> str:
    """Bind a trace identifier to the logging context."""

    configure_logging()
    resolved = trace_id or os.getenv("LOUSA_TRACE_ID") or uuid.uuid4().hex
    _TRACE_ID.set(resolved)
    bind_contextvars(trace_id=resolved)
    return resolved


def bind_context(**values: Any) -> dict[str, Any]:
    """Bind additional key-value pairs to the structured logging context."""

    configure_logging()
    bind_contextvars(**values)
    return get_contextvars()


def get_trace_id() -> str | None:
    """Return the active trace identifier, if one is bound."""

    return _TRACE_ID.get()


def clear_trace() -> None:
    """Clear the trace identifier and any bound structured logging context."""

    _TRACE_ID.set(None)
    clear_contextvars()
