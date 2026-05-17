"""Output formatting: rich table, JSON, CSV."""

from __future__ import annotations

import csv
import io
import json
import sys
from enum import Enum
from typing import Any

import pandas as pd
from rich.console import Console
from rich.table import Table


class OutputFormat(str, Enum):
    table = "table"
    json = "json"
    csv = "csv"


def _is_single_dict(data: Any) -> bool:
    """Check if data is a single dict (not a list of dicts)."""
    return isinstance(data, dict) and not isinstance(data, list)


def _to_records(data: Any) -> list[dict]:
    """Convert various data types to list of dicts for rendering."""
    if isinstance(data, list):
        return data
    if isinstance(data, pd.DataFrame):
        return data.to_dict(orient="records")
    if isinstance(data, dict):
        return [data]
    return [{"value": str(data)}]


def render(
    data: Any,
    fmt: OutputFormat = OutputFormat.table,
    title: str | None = None,
    columns: list[str] | None = None,
) -> None:
    """Render data to stdout in the specified format."""
    if fmt == OutputFormat.json:
        _render_json(data)
    elif fmt == OutputFormat.csv:
        _render_csv(data)
    else:
        _render_table(data, title=title, columns=columns)


def _render_json(data: Any) -> None:
    """Render as JSON to stdout."""
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _render_csv(data: Any) -> None:
    """Render as CSV to stdout."""
    records = _to_records(data)
    if not records:
        return
    writer = csv.DictWriter(sys.stdout, fieldnames=records[0].keys())
    writer.writeheader()
    for row in records:
        writer.writerow({k: str(v) for k, v in row.items()})


def _render_table(
    data: Any,
    title: str | None = None,
    columns: list[str] | None = None,
) -> None:
    """Render as rich table to stdout."""
    # Single dict -> key-value table
    if _is_single_dict(data):
        _render_kv_table(data, title)
        return

    records = _to_records(data)
    if not records:
        return

    is_tty = sys.stdout.isatty()
    console = Console(force_terminal=is_tty)

    table = Table(title=title, show_lines=False, pad_edge=False)
    keys = columns if columns else list(records[0].keys())

    for key in keys:
        table.add_column(str(key))

    for row in records:
        vals = [str(row.get(k, "")) for k in keys]
        table.add_row(*vals)

    console.print(table)


def _render_kv_table(data: dict, title: str | None = None) -> None:
    """Render a single dict as a 2-column key-value table."""
    is_tty = sys.stdout.isatty()
    console = Console(force_terminal=is_tty)

    table = Table(title=title, show_lines=False, pad_edge=False)
    table.add_column("字段", style="bold cyan")
    table.add_column("值")

    for k, v in data.items():
        table.add_row(str(k), str(v))

    console.print(table)
