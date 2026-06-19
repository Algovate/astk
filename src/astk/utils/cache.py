"""Cache helpers for northbound data and other persisted state."""

from __future__ import annotations

import csv
import io
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
    rows: dict[str, list[str]] = {}
    if path.exists():
        with path.open(newline="") as f:
            reader = csv.reader(f)
            try:
                next(reader)  # skip header
            except StopIteration:
                pass
            for parts in reader:
                if len(parts) == 3:
                    rows[parts[0]] = parts
    rows[date] = [date, str(hgt), str(sgt)]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "hgt_yi", "sgt_yi"])
    for d in sorted(rows.keys()):
        writer.writerow(rows[d])

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
