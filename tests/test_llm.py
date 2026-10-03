import groq
import httpx

from core import llm


def test_clean_thinking_tags():
    raw = "<think>secret\nreasoning</think>Answer<thought>x</thought> here"
    assert llm.clean_thinking_tags(raw) == "Answer here"


def test_describe_error_authentication():
    response = httpx.Response(401, request=httpx.Request("GET", "https://api.groq.com"))
    err = groq.AuthenticationError("bad key", response=response, body=None)
    assert "invalid" in llm.describe_error(err).lower()


def test_describe_error_generic():
    assert llm.describe_error(ValueError("boom")) == "boom"
