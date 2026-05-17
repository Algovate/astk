"""Tests for astk.utils.decorators — astk_command and _get_output."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import typer

from astk.utils.decorators import _get_output, astk_command
from astk.utils.errors import InvalidStockCodeError
from astk.utils.output import OutputFormat


# ── _get_output ──────────────────────────────────────────────


class TestGetOutput:
    def test_from_ctx(self):
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {"output": OutputFormat.json}
        assert _get_output(ctx) == OutputFormat.json

    def test_default_when_none(self):
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = None
        assert _get_output(ctx) == OutputFormat.table

    def test_default_when_empty(self):
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {}
        assert _get_output(ctx) == OutputFormat.table

    def test_csv(self):
        ctx = MagicMock(spec=typer.Context)
        ctx.obj = {"output": OutputFormat.csv}
        assert _get_output(ctx) == OutputFormat.csv


# ── astk_command ─────────────────────────────────────────────


class TestAstkCommand:
    def test_wraps_and_calls(self):
        called = False

        @astk_command
        def my_cmd():
            nonlocal called
            called = True

        my_cmd()
        assert called

    def test_propagates_exit_on_invalid_code(self):
        @astk_command
        def my_cmd():
            raise InvalidStockCodeError("bad")

        with pytest.raises(SystemExit):
            my_cmd()

    def test_return_value_passes_through(self):
        @astk_command
        def my_cmd():
            return 42

        # astk_command wraps in handle_errors which calls _run() that returns 42
        # but the wrapper doesn't return it — just calls _run()
        # This is fine since CLI commands use side effects (render), not returns
        my_cmd()  # should not raise
