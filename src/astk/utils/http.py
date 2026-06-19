"""Shared HTTP session for all astk API calls."""

from __future__ import annotations

import functools

import requests

from astk.utils.constants import DEFAULT_UA
from astk.utils.errors import DataSourceError


@functools.lru_cache(maxsize=1)
def get_session() -> requests.Session:
    """Return a shared requests.Session with default headers."""
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_UA})
    return session


def _raise_for_status(resp: requests.Response, url: str) -> requests.Response:
    """Raise DataSourceError on non-2xx so handle_errors maps it cleanly.

    Transport errors (Timeout/ConnectionError) are left as OSError so the
    network-retry path in handle_errors still applies.
    """
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise DataSourceError(f"HTTP {resp.status_code}: {url}") from e
    return resp


def http_get(
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: int = 15,
) -> requests.Response:
    """GET request via the shared session."""
    resp = get_session().get(url, headers=headers, params=params, timeout=timeout)
    return _raise_for_status(resp, url)


def http_post(
    url: str,
    *,
    headers: dict | None = None,
    json: dict | None = None,
    timeout: int = 30,
) -> requests.Response:
    """POST request via the shared session."""
    resp = get_session().post(url, headers=headers, json=json, timeout=timeout)
    return _raise_for_status(resp, url)
