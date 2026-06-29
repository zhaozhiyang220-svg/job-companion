from pydantic import BaseModel

from src.ai import json_parse


class _M(BaseModel):
    done: bool = False
    next_question: str = ""


def test_plain_json() -> None:
    assert json_parse.loads('{"a": 1}') == {"a": 1}


def test_fenced_json() -> None:
    raw = '```json\n{"done": false, "next_question": "tell me more"}\n```'
    assert json_parse.loads(raw)["next_question"] == "tell me more"


def test_prose_wrapped_json() -> None:
    raw = '好的，这是结果：\n{"done": true}\n希望对你有帮助'
    assert json_parse.loads(raw) == {"done": True}


def test_validate_fenced() -> None:
    raw = '```\n{"done": true, "next_question": "x"}\n```'
    m = json_parse.validate(_M, raw)
    assert m.done is True and m.next_question == "x"
