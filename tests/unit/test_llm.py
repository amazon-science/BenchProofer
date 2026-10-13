# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Model providers.

Nothing here talks to a model. What is worth testing about a provider is the part
that is not the network: the cassette key a recorded request is filed under, what a
recording writes, and what a provider does when the API rejects a field it used to
accept.
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar

import httpx
import pytest

from benchproofer.errors import ProviderError
from benchproofer.llm.anthropic import DEFAULT_MODEL, AnthropicProvider
from benchproofer.llm.base import Completion, Message, Provider, ProviderConfig, request_digest
from benchproofer.llm.null import NullProvider
from benchproofer.llm.openai import DEFAULT_BASE_URL, OpenAICompatibleProvider
from benchproofer.llm.record import Recorder, cassette_path
from benchproofer.util.fsio import read_json

MESSAGES = [Message.user("draft a specification")]
#: The non-conversation half of a request, as `request_digest` takes it.
REQUEST = {"system": "be brief", "model": "a-model", "max_tokens": 64, "temperature": 0.0}
#: What an OpenAI-compatible server answers with. The model it names is not the one
#: that was asked for, which is what a server that resolves an alias does.
COMPLETION = {
    "model": "a-model-0125",
    "choices": [{"message": {"content": "drafted"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 22},
}


class Answers(Provider):
    """A provider with one thing to say, so a recording can be made of it."""

    name: ClassVar[str] = "answers"

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Say it."""
        return Completion(
            text="drafted",
            model="a-model",
            stop_reason="end_turn",
            input_tokens=11,
            output_tokens=22,
        )


class Rejection(Exception):
    """What an SDK raises for a request the API refused, as far as this code cares."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.status_code = 400


class FakeStream:
    """What the SDK hands back for a streamed request: a context manager."""

    def __init__(self, message: SimpleNamespace) -> None:
        self.message = message
        self.closed = False

    def __enter__(self) -> FakeStream:
        return self

    def __exit__(self, *_: object) -> None:
        self.closed = True

    def get_final_message(self) -> SimpleNamespace:
        """The message the events add up to."""
        return self.message


class FakeClient:
    """The Anthropic messages client, without the API behind it."""

    def __init__(self, *, rejects_temperature: bool = False) -> None:
        self.rejects_temperature = rejects_temperature
        self.requests: list[dict[str, Any]] = []
        self.streams: list[FakeStream] = []

    @property
    def messages(self) -> FakeClient:
        """The SDK nests `stream` under `messages`; this object stands in for both."""
        return self

    def stream(self, **request: Any) -> FakeStream:
        """Record the request and answer it, or refuse it the way a new model does.

        The SDK sends the request when the stream is entered, so a refusal surfaces
        there rather than here; raising from this call is the same thing to a caller
        that only ever uses the result as a context manager.
        """
        self.requests.append(request)
        if self.rejects_temperature and "temperature" in request:
            raise Rejection("Error code: 400 - `temperature` is deprecated for this model.")
        stream = FakeStream(
            SimpleNamespace(
                # A current model returns its reasoning alongside its answer.
                content=[
                    SimpleNamespace(type="thinking", thinking="..."),
                    SimpleNamespace(type="text", text="drafted"),
                ],
                model=str(request["model"]),
                stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=11, output_tokens=22),
            )
        )
        self.streams.append(stream)
        return stream


def provider_for(
    client: FakeClient, monkeypatch: pytest.MonkeyPatch, **overrides: Any
) -> AnthropicProvider:
    """An Anthropic provider whose requests reach `client` instead of the API."""
    provider = AnthropicProvider(ProviderConfig(model="a-model", **overrides))
    monkeypatch.setattr(provider, "_client", lambda: client)
    return provider


class Endpoint:
    """A chat-completions server, without the server.

    One status code per attempt, the last one repeating, so a test can say "rate
    limited, then fine" and then look at what the provider did about it.
    """

    def __init__(self, *statuses: int, document: dict[str, Any] | None = None) -> None:
        self.statuses = statuses or (httpx.codes.OK,)
        self.document = COMPLETION if document is None else document
        self.sent: list[dict[str, Any]] = []

    def post(self, url: str, **request: Any) -> httpx.Response:
        """Answer one request, as `httpx.post` would."""
        self.sent.append({"url": url, **request})
        status = self.statuses[min(len(self.sent), len(self.statuses)) - 1]
        return httpx.Response(
            status_code=status,
            json=self.document if status == httpx.codes.OK else {"error": "not this time"},
            request=httpx.Request("POST", url),
        )


def openai_for(
    endpoint: Endpoint, monkeypatch: pytest.MonkeyPatch, **overrides: Any
) -> OpenAICompatibleProvider:
    """An OpenAI-compatible provider whose requests reach `endpoint` instead of a server."""
    monkeypatch.setattr(httpx, "post", endpoint.post)
    # A retried request waits before the next attempt, which a test suite should not.
    monkeypatch.setattr(time, "sleep", lambda _: None)
    monkeypatch.setenv("OPENAI_API_KEY", "a-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    return OpenAICompatibleProvider(ProviderConfig(**{"model": "a-model", **overrides}))


def key_for(messages: list[Message], **overrides: Any) -> str:
    """The cassette key for `REQUEST`, with any field replaced."""
    return request_digest(messages, **{**REQUEST, **overrides})


def test_the_cassette_key_is_the_whole_request_and_nothing_else() -> None:
    key = key_for(MESSAGES)

    assert key == key_for(list(MESSAGES))
    assert key != key_for(MESSAGES, system="be thorough")
    assert key != key_for(MESSAGES, model="another-model")
    assert key != key_for(MESSAGES, max_tokens=65)
    assert key != key_for(MESSAGES, temperature=0.5)
    assert key != key_for([Message.user("something else")])


def test_a_recording_files_the_request_and_its_answer_under_the_request_s_key(
    tmp_path: Path,
) -> None:
    config = ProviderConfig(model="a-model", cassette_dir=tmp_path)

    recorded = Recorder(Answers(), config).complete(MESSAGES, system="be brief", max_tokens=64)

    (cassette,) = tmp_path.glob("*.json")
    assert cassette == cassette_path(tmp_path, key_for(MESSAGES))
    document = read_json(cassette)
    assert document["request"]["messages"] == [{"role": "user", "content": MESSAGES[0].content}]
    assert (document["request"]["system"], document["request"]["max_tokens"]) == (
        "be brief",
        64,
    )
    assert document["completion"]["text"] == recorded.text
    assert document["completion"]["output_tokens"] == recorded.output_tokens


def test_the_default_provider_refuses_and_says_what_to_select_instead() -> None:
    with pytest.raises(ProviderError, match="select one with --provider"):
        NullProvider().complete(MESSAGES)


def test_a_model_that_refuses_a_temperature_is_asked_again_without_one_for_the_rest_of_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient(rejects_temperature=True)
    provider = provider_for(client, monkeypatch)

    completion = provider.complete(MESSAGES, max_tokens=64)
    provider.complete(MESSAGES)

    assert completion.text == "drafted"
    assert (completion.input_tokens, completion.output_tokens) == (11, 22)
    assert ["temperature" in request for request in client.requests] == [True, False, False]


def test_a_model_that_accepts_a_temperature_is_asked_once_with_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient()

    provider_for(client, monkeypatch).complete(MESSAGES, temperature=0.25)

    assert [request["temperature"] for request in client.requests] == [0.25]


def test_the_answer_is_streamed_and_the_stream_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drafting spends minutes on one answer, which a silent request does not survive.

    A model that is given a large output budget and uses it sends nothing back for
    long enough to look like a stalled connection, so an unstreamed request is
    abandoned at the timeout and tried again at full length.
    """
    client = FakeClient()

    completion = provider_for(client, monkeypatch).complete(MESSAGES)

    assert completion.text == "drafted"
    assert [stream.closed for stream in client.streams] == [True]


def test_an_empty_system_prompt_is_left_out_rather_than_sent_as_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient()

    provider_for(client, monkeypatch).complete(MESSAGES)

    assert "system" not in client.requests[0]


def test_a_refusal_that_is_not_about_sampling_is_reported_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Broken(FakeClient):
        def stream(self, **request: Any) -> FakeStream:
            self.requests.append(request)
            raise Rejection("Error code: 400 - max_tokens is too large")

    client = Broken()
    provider = provider_for(client, monkeypatch)

    with pytest.raises(ProviderError, match="anthropic request failed: Rejection"):
        provider.complete(MESSAGES)
    assert len(client.requests) == 1


def test_an_offline_run_refuses_a_provider_that_needs_the_network() -> None:
    provider = AnthropicProvider(ProviderConfig(model="a-model", offline=True))

    with pytest.raises(ProviderError, match="this run is offline"):
        provider.complete(MESSAGES)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("us.anthropic.claude-opus-5", "AWS_REGION is not set"),
        (DEFAULT_MODEL, "ANTHROPIC_API_KEY is not set"),
    ],
)
def test_availability_names_the_credential_the_model_id_calls_for(
    model: str, expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("anthropic")
    for name in ("ANTHROPIC_API_KEY", "AWS_REGION", "AWS_DEFAULT_REGION"):
        monkeypatch.delenv(name, raising=False)

    report = AnthropicProvider(ProviderConfig(model=model)).availability()

    assert not report.available
    assert expected in report.detail


def test_a_chat_completion_is_read_back_as_what_the_server_answered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    endpoint = Endpoint()

    completion = openai_for(endpoint, monkeypatch).complete(
        MESSAGES, system="be brief", max_tokens=64
    )

    assert (completion.text, completion.stop_reason) == ("drafted", "stop")
    # The model that answered, not the alias that was asked for: a cassette recorded
    # here has to say which model actually produced the text.
    assert completion.model == "a-model-0125"
    assert (completion.input_tokens, completion.output_tokens) == (11, 22)

    request = endpoint.sent[0]
    assert request["url"] == f"{DEFAULT_BASE_URL}/chat/completions"
    assert request["headers"]["authorization"] == "Bearer a-key"
    assert [message["role"] for message in request["json"]["messages"]] == ["system", "user"]
    assert request["json"]["max_tokens"] == 64


def test_a_transient_failure_is_tried_again(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = Endpoint(httpx.codes.TOO_MANY_REQUESTS, httpx.codes.OK)

    completion = openai_for(endpoint, monkeypatch, max_retries=2).complete(MESSAGES)

    assert completion.text == "drafted"
    assert len(endpoint.sent) == 2


def test_a_request_the_server_refuses_is_not_tried_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rejected request is rejected the same way however often it is sent."""
    endpoint = Endpoint(httpx.codes.BAD_REQUEST)
    provider = openai_for(endpoint, monkeypatch, max_retries=3)

    with pytest.raises(ProviderError, match="HTTP 400"):
        provider.complete(MESSAGES)
    assert len(endpoint.sent) == 1


def test_an_answer_that_is_not_a_chat_completion_names_the_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A server that speaks a different protocol is a configuration mistake."""
    provider = openai_for(Endpoint(document={"result": "drafted"}), monkeypatch)
    complaint = f"unexpected response shape from {DEFAULT_BASE_URL}"

    with pytest.raises(ProviderError, match=complaint):
        provider.complete(MESSAGES)


@pytest.mark.parametrize(
    ("key", "base_url", "available", "expected"),
    [
        ("a-key", "", True, DEFAULT_BASE_URL),
        # A self-hosted server commonly wants no key at all, so an absent one is not
        # a reason to report the provider unusable.
        ("", "http://localhost:8000/v1/", True, "no key set"),
        ("", "", False, "OPENAI_API_KEY is not set"),
    ],
)
def test_a_local_endpoint_needs_no_key_and_the_hosted_one_says_so(
    key: str,
    base_url: str,
    available: bool,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in (("OPENAI_API_KEY", key), ("OPENAI_BASE_URL", base_url)):
        monkeypatch.delenv(name, raising=False)
        if value:
            monkeypatch.setenv(name, value)

    report = OpenAICompatibleProvider(ProviderConfig(model="a-model")).availability()

    assert report.available is available
    assert expected in report.detail


def test_an_offline_run_reaches_no_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = Endpoint()
    provider = openai_for(endpoint, monkeypatch, offline=True)

    with pytest.raises(ProviderError, match="this run is offline"):
        provider.complete(MESSAGES)
    assert not endpoint.sent


def test_an_endpoint_that_serves_many_models_has_to_be_told_which_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = openai_for(Endpoint(), monkeypatch, model="")

    with pytest.raises(ProviderError, match="needs a model id"):
        provider.complete(MESSAGES)
