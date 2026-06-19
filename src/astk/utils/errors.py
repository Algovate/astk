"""Custom exceptions and error handling."""

from __future__ import annotations

import functools
import os
import time
from typing import Callable

from rich.console import Console

stderr = Console(stderr=True)


class AStockError(Exception):
    """Base exception for astk."""


class InvalidStockCodeError(AStockError):
    """Bad stock code format."""


class DataUnavailableError(AStockError):
    """No data returned (non-trading day, empty response)."""


class NetworkTimeoutError(AStockError):
    """Request timeout."""


class AuthenticationError(AStockError):
    """iwencai 401 / missing API key."""


class DataSourceError(AStockError):
    """Upstream API returned error."""


def handle_errors(func: Callable) -> Callable:
    """Decorator that wraps CLI commands with error handling and retry."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except InvalidStockCodeError as e:
                stderr.print(f"[red]错误:[/red] {e}")
                raise SystemExit(1)
            except ValueError as e:
                # Bad user input (e.g. malformed --date). Not retried.
                stderr.print(f"[red]错误:[/red] {e}")
                raise SystemExit(1)
            except DataUnavailableError as e:
                stderr.print(f"[yellow]无数据:[/yellow] {e}")
                raise SystemExit(0)
            except AuthenticationError as e:
                stderr.print(f"[red]认证失败:[/red] {e}")
                raise SystemExit(1)
            except DataSourceError as e:
                stderr.print(f"[red]数据源错误:[/red] {e}")
                raise SystemExit(1)
            except (ConnectionError, TimeoutError, OSError) as e:
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    stderr.print(f"[yellow]网络超时，{wait}s 后重试 ({attempt + 1}/{max_retries})...[/yellow]")
                    time.sleep(wait)
                    continue
                stderr.print(f"[red]网络错误:[/red] {e}")
                raise SystemExit(1)
            except Exception as e:
                if os.environ.get("ASTK_DEBUG"):
                    raise
                stderr.print(f"[red]未预期错误:[/red] {e}")
                raise SystemExit(1)

    return wrapper
