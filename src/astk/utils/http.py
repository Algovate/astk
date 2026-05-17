"""Shared HTTP session for all astk API calls."""

from __future__ import annotations

import functools

import requests

from astk.utils.constants import DEFAULT_UA


@functools.lru_cache(maxsize=1)
def get_session() -> requests.Session:
    """Return a shared requests.Session with default headers."""
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_UA})
    return session


def http_get(
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: int = 15,
) -> requests.Response:
    """GET request via the shared session."""
    return get_session().get(url, headers=headers, params=params, timeout=timeout)


def http_post(
    url: str,
    *,
    headers: dict | None = None,
    json: dict | None = None,
    timeout: int = 30,
) -> requests.Response:
    """POST request via the shared session."""
    return get_session().post(url, headers=headers, json=json, timeout=timeout)
