"""Tests for astk.utils.errors — exception hierarchy and handle_errors."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import requests

from astk.utils.errors import (
    AStockError,
    AuthenticationError,
    DataUnavailableError,
    DataSourceError,
    InvalidDateError,
    InvalidStockCodeError,
    NetworkTimeoutError,
    handle_errors,
)


# ── Exception hierarchy ──────────────────────────────────────


class TestExceptionHierarchy:
    @pytest.mark.parametrize(
        "exc_cls",
        [
            InvalidStockCodeError,
            InvalidDateError,
            DataUnavailableError,
            NetworkTimeoutError,
            AuthenticationError,
            DataSourceError,
        ],
    )
    def test_inherits_from_base(self, exc_cls):
        assert issubclass(exc_cls, AStockError)

    def test_base_inherits_from_exception(self):
        assert issubclass(AStockError, Exception)


# ── handle_errors ────────────────────────────────────────────


class TestHandleErrors:
    def test_success(self):
        @handle_errors
        def fn():
            return 42
        assert fn() == 42

    def test_invalid_stock_code(self):
        @handle_errors
        def fn():
            raise InvalidStockCodeError("bad code")
        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 1

    def test_data_unavailable(self):
        @handle_errors
        def fn():
            raise DataUnavailableError("no data")
        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 0

    def test_authentication_error(self):
        @handle_errors
        def fn():
            raise AuthenticationError("no key")
        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 1

    def test_data_source_error(self):
        @handle_errors
        def fn():
            raise DataSourceError("upstream fail")
        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 1

    @patch("astk.utils.errors.time.sleep")
    def test_network_retries_exhausted(self, mock_sleep):
        call_count = 0

        @handle_errors
        def fn():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("timeout")

        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert call_count == 3
        assert exc_info.value.code == 1
        assert mock_sleep.call_count == 2

    @patch("astk.utils.errors.time.sleep")
    def test_network_succeeds_second_try(self, mock_sleep):
        call_count = 0

        @handle_errors
        def fn():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("timeout")
            return "ok"

        result = fn()
        assert result == "ok"
        assert call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch("astk.utils.errors.time.sleep")
    def test_timeout_retries(self, mock_sleep):
        call_count = 0

        @handle_errors
        def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timed out")
            return "ok"

        result = fn()
        assert result == "ok"
        assert call_count == 3

    def test_unexpected_error(self):
        @handle_errors
        def fn():
            raise RuntimeError("surprise")
        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 1

    def test_invalid_date_treated_as_user_input(self):
        @handle_errors
        def fn():
            raise InvalidDateError("bad date")
        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 1

    @patch("astk.utils.errors.time.sleep")
    def test_json_decode_error_uses_network_retry_path(self, mock_sleep):
        call_count = 0

        @handle_errors
        def fn():
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.JSONDecodeError("bad json", "", 0)

        with pytest.raises(SystemExit) as exc_info:
            fn()
        assert exc_info.value.code == 1
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("astk.utils.errors.os")
    def test_debug_env_reraises(self, mock_os):
        mock_os.environ.get.return_value = "1"
        caught = False

        @handle_errors
        def fn():
            raise RuntimeError("boom")

        try:
            fn()
        except RuntimeError:
            caught = True
        assert caught

    @patch("astk.utils.errors.os")
    def test_no_debug_swallows(self, mock_os):
        mock_os.environ.get.return_value = ""

        @handle_errors
        def fn():
            raise RuntimeError("boom")

        with pytest.raises(SystemExit):
            fn()
