"""Cache helpers for northbound data and other persisted state."""

from __future__ import annotations

import csv
import io
import tempfile
from pathlib import Path

import pandas as pd


def cache_dir() -> Path:
    """Return the astk cache directory, creating it if needed."""
    p = Path.home() / ".astk" / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def northbound_cache_path() -> Path:
    """Return path to northbound daily CSV cache."""
    return cache_dir() / "northbound_daily.csv"


def save_northbound_snapshot(date: str, hgt: float, sgt: float) -> None:
    """Write/update a day's northbound closing data to CSV cache.

    Uses atomic write (write to temp, then rename) to avoid data loss
    from concurrent processes.
    """
    path = northbound_cache_path()
    rows: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().strip().split("\n")[1:]:
            parts = line.split(",")
            if len(parts) == 3:
                rows[parts[0]] = line
    rows[date] = f"{date},{hgt},{sgt}"

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "hgt_yi", "sgt_yi"])
    for d in sorted(rows.keys()):
        writer.writerow(rows[d].split(","))

    tmp = path.with_suffix(".tmp")
    tmp.write_text(buf.getvalue())
    tmp.replace(path)


def load_northbound_history(n: int = 20) -> pd.DataFrame:
    """Read last N days of northbound history from cache."""
    path = northbound_cache_path()
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df.tail(n)
