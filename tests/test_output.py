"""Tests for astk.utils.output — rendering and formatting."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from astk.utils.output import (
    OutputFormat,
    _is_single_dict,
    _sanitize_csv_value,
    _to_records,
    render,
)


# ── OutputFormat ─────────────────────────────────────────────


class TestOutputFormat:
    def test_enum_values(self):
        assert OutputFormat.table == "table"
        assert OutputFormat.json == "json"
        assert OutputFormat.csv == "csv"


# ── _is_single_dict ──────────────────────────────────────────


class TestIsSingleDict:
    def test_dict_true(self):
        assert _is_single_dict({"a": 1}) is True

    def test_list_false(self):
        assert _is_single_dict([{"a": 1}]) is False

    def test_str_false(self):
        assert _is_single_dict("hello") is False

    def test_int_false(self):
        assert _is_single_dict(42) is False

    def test_empty_dict_true(self):
        assert _is_single_dict({}) is True


# ── _sanitize_csv_value ─────────────────────────────────────


class TestSanitizeCsvValue:
    @pytest.mark.parametrize("value", ["=1+1", "=CMD", "=import"])
    def test_equals(self, value):
        assert _sanitize_csv_value(value).startswith("'=")

    def test_plus(self):
        assert _sanitize_csv_value("+cmd") == "'+cmd"

    def test_minus(self):
        assert _sanitize_csv_value("-1+1") == "'-1+1"

    def test_at(self):
        assert _sanitize_csv_value("@SUM") == "'@SUM"

    def test_tab(self):
        assert _sanitize_csv_value("\tdata") == "'\tdata"

    def test_carriage_return(self):
        assert _sanitize_csv_value("\rdata") == "'\rdata"

    def test_safe_value(self):
        assert _sanitize_csv_value("hello") == "hello"

    def test_empty(self):
        assert _sanitize_csv_value("") == ""

    def test_number(self):
        assert _sanitize_csv_value("42.5") == "42.5"


# ── _to_records ──────────────────────────────────────────────


class TestToRecords:
    def test_list_passthrough(self):
        data = [{"a": 1}, {"a": 2}]
        assert _to_records(data) == data

    def test_dict_wrapped(self):
        result = _to_records({"a": 1})
        assert result == [{"a": 1}]

    def test_dataframe_converted(self):
        df = pd.DataFrame({"x": [1, 2]})
        result = _to_records(df)
        assert len(result) == 2
        assert result[0]["x"] == 1

    def test_scalar_wrapped(self):
        result = _to_records(42)
        assert result == [{"value": "42"}]


# ── render JSON ──────────────────────────────────────────────


class TestRenderJson:
    def test_dict(self, capsys):
        render({"name": "test", "price": 100}, OutputFormat.json)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["name"] == "test"

    def test_list(self, capsys):
        render([{"a": 1}], OutputFormat.json)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert isinstance(parsed, list)

    def test_dataframe(self, capsys):
        df = pd.DataFrame({"x": [1]})
        render(df, OutputFormat.json)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed[0]["x"] == 1


# ── render CSV ───────────────────────────────────────────────


class TestRenderCsv:
    def test_list_with_header(self, capsys):
        render([{"name": "test", "val": 42}], OutputFormat.csv)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert "name" in lines[0]
        assert "test" in lines[1]

    def test_sanitization(self, capsys):
        render([{"name": "=DANGER"}], OutputFormat.csv)
        out = capsys.readouterr().out
        assert "'=DANGER" in out

    def test_empty_list(self, capsys):
        render([], OutputFormat.csv)
        out = capsys.readouterr().out
        assert out == ""

    def test_dict_as_kv(self, capsys):
        render({"key1": "val1"}, OutputFormat.csv)
        out = capsys.readouterr().out
        assert "key1" in out
        assert "val1" in out
