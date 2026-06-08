import pytest

from src.llm_client import parse_json_response


def test_plain_json():
    assert parse_json_response('{"a": 1}') == {"a": 1}


def test_json_fence():
    raw = '```json\n{"a": 1, "b": "x"}\n```'
    assert parse_json_response(raw) == {"a": 1, "b": "x"}


def test_bare_fence():
    raw = '```\n{"a": 1}\n```'
    assert parse_json_response(raw) == {"a": 1}


def test_surrounding_whitespace():
    assert parse_json_response('  \n {"a": 1} \n ') == {"a": 1}


def test_invalid_raises():
    with pytest.raises(ValueError):
        parse_json_response("not json at all")
