# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import os

from structlog.contextvars import get_contextvars

from lousa import logging as lousa_logging


def setup_function() -> None:
    lousa_logging.configure_logging(force=True)
    lousa_logging.clear_trace()
    os.environ.pop("LOUSA_TRACE_ID", None)


def test_bind_trace_explicit_sets_context() -> None:
    trace_id = lousa_logging.bind_trace("trace-123")
    context = get_contextvars()

    assert trace_id == "trace-123"
    assert context["trace_id"] == "trace-123"
    assert lousa_logging.get_trace_id() == "trace-123"


def test_bind_trace_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv("LOUSA_TRACE_ID", "env-trace")

    trace_id = lousa_logging.bind_trace()
    context = get_contextvars()

    assert trace_id == "env-trace"
    assert context["trace_id"] == "env-trace"


def test_bind_context_adds_fields() -> None:
    lousa_logging.bind_trace("ctx-trace")
    lousa_logging.bind_context(operation="unit-test", component="cli")

    context = get_contextvars()

    assert context["trace_id"] == "ctx-trace"
    assert context["operation"] == "unit-test"
    assert context["component"] == "cli"
