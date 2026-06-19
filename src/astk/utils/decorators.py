"""CLI command helpers: decorator to replace the _run() boilerplate."""

from __future__ import annotations

import functools
from typing import Callable

import typer

from astk.utils.errors import handle_errors
from astk.utils.output import OutputFormat


def _get_output(ctx: typer.Context) -> OutputFormat:
    """Extract output format from Typer context."""
    return ctx.obj.get("output", OutputFormat.table) if ctx.obj else OutputFormat.table


def astk_command(func: Callable) -> Callable:
    """Decorator that wraps a CLI command with error handling.

    Replaces the boilerplate pattern of:
        @handle_errors
        def _run():
            ...
        _run()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        @handle_errors
        def _run():
            return func(*args, **kwargs)
        return _run()

    return wrapper
