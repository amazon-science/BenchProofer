# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Model providers for the evaluation harness.

A thin `Provider` interface; all implementations normalize to one `Turn`.

  BedrockProvider — boto3 converse. A FRESH Session per provider instance
    re-reads ~/.aws/credentials (Bedrock credentials are short-lived and
    rotate). On an expiry error the client is rebuilt and retried; persistent
    expiry raises CredentialsExpired so the driver PARKS the instance for resume.

  OpenAIProvider — `openai` SDK against any OpenAI-compatible base_url.

Tools are provider-agnostic ToolSpecs; each provider renders its own schema.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any


def resolve_region(fallback: str) -> str:
    """The region to talk to, given a preset's own default.

    Which region hosts a model is a property of the ACCOUNT, not of this
    pipeline, so the presets below carry a default rather than a constant. The
    defaults are the regions each preset's model is reachable in from the account
    it was written for; another account may have the same model somewhere else, or
    may not be allowed to call that region at all, and then every request fails
    identically with an access error that names the model rather than the region.

    `SBU_BEDROCK_REGION` overrides all presets. `AWS_REGION` and
    `AWS_DEFAULT_REGION` are honored next because they are what the rest of an
    AWS toolchain already reads, and a caller who has set them does not expect
    this one library to ignore them -- boto3 would not, but these providers pass
    `region_name` explicitly, which takes precedence over the environment.
    """
    for name in ("SBU_BEDROCK_REGION", "AWS_REGION", "AWS_DEFAULT_REGION"):
        # A variable exported empty means unset; taking it literally would build a
        # client with region_name="" and fail at the first call, not at config time.
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    return fallback


@dataclass
class ToolSpec:
    name: str
    description: str
    # JSON-schema "properties" dict + required list
    properties: dict
    required: list[str]


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class Turn:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = ""          # "tool_use" | "end_turn" | "max_tokens" | ...
    usage: dict = field(default_factory=dict)
    raw: Any = None                # the provider's raw assistant message (for history)


class CredentialsExpired(Exception):
    """Expired credentials not recovered within the retry budget — the driver
    parks the instance."""


class ProviderError(Exception):
    """A non-credential, non-retryable provider failure."""


# Conversations are provider-neutral message lists translated per provider:
#   {"role": "user"|"assistant", "content": [blocks]}, block = {"text"} |
#   {"tool_use": {id,name,input}} (assistant) |
#   {"tool_result": {id,content,is_error}} (user)


# "creds rotated / invalid" — rebuild the session
_BEDROCK_CRED_ERRORS = {
    "ExpiredTokenException", "ExpiredToken",
    "UnrecognizedClientException", "InvalidSignatureException",
    "AccessDeniedException",  # often a freshly-expired/rotated key on Bedrock
}
# throttling / transient — backoff+retry, not a creds rebuild
_BEDROCK_THROTTLE = {"ThrottlingException", "TooManyRequestsException",
                     "ServiceUnavailableException", "ModelTimeoutException",
                     "InternalServerException"}


class BedrockProvider:
    def __init__(self, model_id: str, region: str = "us-west-2",
                 max_tokens: int = 4096, omit_temperature: bool | None = None,
                 cred_retries: int = 4):
        self.model_id = model_id
        self.region = region
        self.max_tokens = max_tokens
        # Opus 4.8 rejects temperature; omit for all anthropic models by default
        self.omit_temperature = (("anthropic" in model_id or "opus" in model_id)
                                 if omit_temperature is None else omit_temperature)
        self.cred_retries = cred_retries
        self._client = None
        self._build_client()

    def _build_client(self):
        """Fresh Session re-reads ~/.aws/credentials (rotated creds)."""
        import boto3
        self._client = boto3.Session().client("bedrock-runtime", region_name=self.region)

    def _tool_config(self, tools: list[ToolSpec]) -> dict:
        return {"tools": [{"toolSpec": {
            "name": t.name, "description": t.description,
            "inputSchema": {"json": {"type": "object", "properties": t.properties,
                                     "required": t.required}},
        }} for t in tools]}

    @staticmethod
    def _to_bedrock_messages(messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            content = []
            for b in m["content"]:
                if "text" in b:
                    content.append({"text": b["text"]})
                elif "tool_use" in b:
                    tu = b["tool_use"]
                    content.append({"toolUse": {"toolUseId": tu["id"], "name": tu["name"],
                                                "input": tu["input"]}})
                elif "tool_result" in b:
                    tr = b["tool_result"]
                    block = {"toolResult": {"toolUseId": tr["id"],
                                            "content": [{"text": tr["content"]}]}}
                    if tr.get("is_error"):
                        block["toolResult"]["status"] = "error"
                    content.append(block)
            out.append({"role": m["role"], "content": content})
        return out

    def chat(self, system: str, messages: list[dict], tools: list[ToolSpec]) -> Turn:
        infcfg: dict = {"maxTokens": self.max_tokens}
        if not self.omit_temperature:
            infcfg["temperature"] = 0.0
        kw = dict(modelId=self.model_id, system=[{"text": system}],
                  messages=self._to_bedrock_messages(messages),
                  inferenceConfig=infcfg)
        if tools:
            kw["toolConfig"] = self._tool_config(tools)

        last_err = None
        for attempt in range(self.cred_retries + 1):
            try:
                resp = self._client.converse(**kw)
                return self._parse(resp)
            except Exception as e:  # noqa: BLE001
                name = type(e).__name__
                resp_obj = getattr(e, "response", None)
                err_code = ""
                if isinstance(resp_obj, dict):
                    err_code = resp_obj.get("Error", {}).get("Code", "")
                err_code = err_code or name
                last_err = e
                if err_code in _BEDROCK_CRED_ERRORS or name in _BEDROCK_CRED_ERRORS:
                    # rotated/expired creds → rebuild session + retry
                    if attempt < self.cred_retries:
                        time.sleep(min(30, 3 * (attempt + 1)))
                        self._build_client()
                        continue
                    raise CredentialsExpired(f"{err_code}: {e}") from e
                if err_code in _BEDROCK_THROTTLE or name in _BEDROCK_THROTTLE:
                    if attempt < self.cred_retries:
                        time.sleep(min(60, 5 * (2 ** attempt)))
                        continue
                    raise ProviderError(f"{err_code} (throttled, gave up): {e}") from e
                raise ProviderError(f"{err_code}: {e}") from e
        raise ProviderError(f"exhausted retries: {last_err}")

    def _parse(self, resp: dict) -> Turn:
        msg = resp["output"]["message"]
        text, calls, neutral = "", [], []
        for b in msg["content"]:
            if "text" in b:
                text += b["text"]
                neutral.append({"text": b["text"]})
            elif "toolUse" in b:
                tu = b["toolUse"]
                calls.append(ToolCall(tu["toolUseId"], tu["name"], tu.get("input", {}) or {}))
                neutral.append({"tool_use": {"id": tu["toolUseId"], "name": tu["name"],
                                             "input": tu.get("input", {}) or {}}})
        # raw is PROVIDER-NEUTRAL so it round-trips through _to_bedrock_messages
        raw = {"role": "assistant", "content": neutral}
        return Turn(text=text, tool_calls=calls, stop_reason=resp.get("stopReason", ""),
                    usage=resp.get("usage", {}) or {}, raw=raw)


class OpenAIProvider:
    """OpenAI-compatible Chat Completions (OpenRouter, vLLM, etc.). For GPT-5.5
    on bedrock-mantle (a Responses-API-only model) use OpenAIResponsesProvider."""

    def __init__(self, model_id: str, base_url: str | None = None,
                 api_key_env: str = "OPENAI_API_KEY", max_tokens: int = 4096,
                 retries: int = 4, extra_headers: dict | None = None):
        import os
        from openai import OpenAI
        key = os.environ.get(api_key_env)
        if not key:
            raise ProviderError(f"{api_key_env} not set (needed for {model_id})")
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.retries = retries
        self._client = OpenAI(base_url=base_url, api_key=key,
                              default_headers=extra_headers or None, max_retries=0)

    def _tools(self, tools: list[ToolSpec]) -> list[dict]:
        return [{"type": "function", "function": {
            "name": t.name, "description": t.description,
            "parameters": {"type": "object", "properties": t.properties,
                           "required": t.required},
        }} for t in tools]

    @staticmethod
    def _to_openai_messages(system: str, messages: list[dict]) -> list[dict]:
        out = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "assistant":
                text = "".join(b["text"] for b in m["content"] if "text" in b)
                tcs = [{"id": b["tool_use"]["id"], "type": "function",
                        "function": {"name": b["tool_use"]["name"],
                                     "arguments": json.dumps(b["tool_use"]["input"])}}
                       for b in m["content"] if "tool_use" in b]
                msg = {"role": "assistant", "content": text or None}
                if tcs:
                    msg["tool_calls"] = tcs
                out.append(msg)
            else:  # user: plain text and/or tool results
                results = [b for b in m["content"] if "tool_result" in b]
                texts = [b["text"] for b in m["content"] if "text" in b]
                if texts:
                    out.append({"role": "user", "content": "\n".join(texts)})
                for b in results:
                    tr = b["tool_result"]
                    out.append({"role": "tool", "tool_call_id": tr["id"],
                                "content": tr["content"]})
        return out

    def chat(self, system: str, messages: list[dict], tools: list[ToolSpec]) -> Turn:
        kw = dict(model=self.model_id,
                  messages=self._to_openai_messages(system, messages),
                  max_tokens=self.max_tokens)
        if tools:
            kw["tools"] = self._tools(tools)
            kw["tool_choice"] = "auto"
        last = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._client.chat.completions.create(**kw)
                return self._parse(resp)
            except Exception as e:  # noqa: BLE001
                last = e
                name = type(e).__name__
                if name in ("AuthenticationError", "PermissionDeniedError"):
                    raise CredentialsExpired(str(e)) from e
                if name in ("RateLimitError", "APITimeoutError", "InternalServerError",
                            "APIConnectionError") and attempt < self.retries:
                    time.sleep(min(60, 5 * (2 ** attempt)))
                    continue
                raise ProviderError(f"{name}: {e}") from e
        raise ProviderError(f"exhausted retries: {last}")

    def _parse(self, resp) -> Turn:
        ch = resp.choices[0]
        msg = ch.message
        calls = []
        for tc in (msg.tool_calls or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            calls.append(ToolCall(tc.id, tc.function.name, args))
        stop = "tool_use" if calls else (ch.finish_reason or "end_turn")
        usage = {}
        if resp.usage:
            usage = {"inputTokens": resp.usage.prompt_tokens,
                     "outputTokens": resp.usage.completion_tokens,
                     "totalTokens": resp.usage.total_tokens}
        # provider-neutral assistant message for history
        content = []
        if msg.content:
            content.append({"text": msg.content})
        for c in calls:
            content.append({"tool_use": {"id": c.id, "name": c.name, "input": c.input}})
        return Turn(text=msg.content or "", tool_calls=calls, stop_reason=stop,
                    usage=usage, raw={"role": "assistant", "content": content})


class OpenAIResponsesProvider:
    """GPT-5.5 on Bedrock's `bedrock-mantle` endpoint (Responses API only).

    Auth: a region-scoped Bedrock bearer token minted from the SigV4 creds per
    provider instance (expires with the temp creds, ~12h). Responses API shape:
    flat `input` items, function_call / function_call_output keyed by call_id,
    plus opaque `reasoning` items that must be echoed back verbatim.
    """

    def __init__(self, model_id: str = "openai.gpt-5.5", region: str = "us-east-1",
                 max_tokens: int = 4096, retries: int = 4):
        self.model_id = model_id
        self.region = region
        self.max_tokens = max_tokens
        self.retries = retries
        self._client = None
        self._build_client()

    def _mint_token(self) -> str:
        from aws_bedrock_token_generator import provide_token
        # must be region-scoped (default-region token => 401); minted fresh
        # from current ~/.aws creds (picks up rotation)
        return provide_token(region=self.region)

    def _build_client(self):
        from openai import OpenAI
        base = f"https://bedrock-mantle.{self.region}.api.aws/openai/v1"
        self._client = OpenAI(base_url=base, api_key=self._mint_token(),
                              max_retries=0, timeout=600)

    def _tools(self, tools: list[ToolSpec]) -> list[dict]:
        # Responses-API tool shape (flat, no nested "function" key)
        return [{"type": "function", "name": t.name, "description": t.description,
                 "parameters": {"type": "object", "properties": t.properties,
                                "required": t.required}} for t in tools]

    def _to_input_items(self, messages: list[dict]) -> list:
        """Neutral messages -> Responses `input` items. Assistant turns with a
        stored raw payload (incl. reasoning items) replay verbatim; otherwise
        items are synthesized."""
        items: list = []
        for m in messages:
            raw = m.get("_responses_raw")
            if m["role"] == "assistant" and raw is not None:
                items.extend(raw)  # echo prior output items verbatim
                continue
            if m["role"] == "assistant":
                text = "".join(b["text"] for b in m["content"] if "text" in b)
                if text:
                    items.append({"role": "assistant", "content": text})
                for b in m["content"]:
                    if "tool_use" in b:
                        tu = b["tool_use"]
                        items.append({"type": "function_call", "call_id": tu["id"],
                                      "name": tu["name"], "arguments": json.dumps(tu["input"])})
            else:  # user
                for b in m["content"]:
                    if "text" in b:
                        items.append({"role": "user", "content": b["text"]})
                    elif "tool_result" in b:
                        tr = b["tool_result"]
                        items.append({"type": "function_call_output",
                                      "call_id": tr["id"], "output": tr["content"]})
        return items

    def chat(self, system: str, messages: list[dict], tools: list[ToolSpec]) -> Turn:
        kw = dict(model=self.model_id, instructions=system,
                  input=self._to_input_items(messages),
                  max_output_tokens=self.max_tokens)
        if tools:
            kw["tools"] = self._tools(tools)
        last = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._client.responses.create(**kw)
                return self._parse(resp)
            except Exception as e:  # noqa: BLE001
                last = e
                name = type(e).__name__
                if name in ("AuthenticationError", "PermissionDeniedError"):
                    # token expired/rotated → re-mint + retry
                    if attempt < self.retries:
                        time.sleep(min(20, 2 * (attempt + 1)))
                        self._build_client()
                        continue
                    raise CredentialsExpired(str(e)) from e
                if name in ("RateLimitError", "APITimeoutError", "InternalServerError",
                            "APIConnectionError") and attempt < self.retries:
                    time.sleep(min(60, 5 * (2 ** attempt)))
                    continue
                raise ProviderError(f"{name}: {e}") from e
        raise ProviderError(f"exhausted retries: {last}")

    def _parse(self, resp) -> Turn:
        text, calls, raw_items = "", [], []
        for it in resp.output:
            t = getattr(it, "type", "")
            # keep raw item: reasoning items MUST be replayed verbatim for
            # multi-turn tool use to work
            raw_items.append(it.model_dump() if hasattr(it, "model_dump") else it)
            if t == "function_call":
                try:
                    args = json.loads(it.arguments or "{}")
                except json.JSONDecodeError:
                    args = {"_raw": it.arguments}
                calls.append(ToolCall(it.call_id, it.name, args))
            elif t == "message":
                for c in getattr(it, "content", []):
                    if getattr(c, "type", "") == "output_text":
                        text += c.text
        usage = {}
        if resp.usage:
            usage = {"inputTokens": resp.usage.input_tokens,
                     "outputTokens": resp.usage.output_tokens,
                     "totalTokens": getattr(resp.usage, "total_tokens",
                                            resp.usage.input_tokens + resp.usage.output_tokens)}
        stop = "tool_use" if calls else "end_turn"
        raw_msg = {"role": "assistant", "content": [], "_responses_raw": raw_items}
        if text:
            raw_msg["content"].append({"text": text})
        for c in calls:
            raw_msg["content"].append({"tool_use": {"id": c.id, "name": c.name, "input": c.input}})
        return Turn(text=text, tool_calls=calls, stop_reason=stop, usage=usage, raw=raw_msg)


def make_provider(spec: dict):
    """spec = {"provider": "bedrock"|"openai"|"openai_responses", "model_id":...}."""
    p = spec.get("provider", "bedrock")
    if p == "bedrock":
        return BedrockProvider(
            model_id=spec["model_id"],
            region=resolve_region(spec.get("region") or "us-west-2"),
            max_tokens=spec.get("max_tokens", 4096),
            omit_temperature=spec.get("omit_temperature"),
        )
    if p == "openai":
        return OpenAIProvider(
            model_id=spec["model_id"],
            base_url=spec.get("base_url"),
            api_key_env=spec.get("api_key_env", "OPENAI_API_KEY"),
            max_tokens=spec.get("max_tokens", 4096),
            extra_headers=spec.get("extra_headers"),
        )
    if p == "openai_responses":
        return OpenAIResponsesProvider(
            model_id=spec.get("model_id", "openai.gpt-5.5"),
            region=resolve_region(spec.get("region") or "us-east-1"),
            max_tokens=spec.get("max_tokens", 4096),
        )
    raise ProviderError(f"unknown provider {p!r}")


# named model presets for the CLI (--model <key>)
MODEL_PRESETS = {
    "opus-5": {"provider": "bedrock", "model_id": "us.anthropic.claude-opus-5",
               "region": "us-west-2"},
    "opus-4.8": {"provider": "bedrock", "model_id": "us.anthropic.claude-opus-4-8",
                 "region": "us-west-2"},
    "sonnet-4.6": {"provider": "bedrock", "model_id": "us.anthropic.claude-sonnet-4-6",
                   "region": "us-west-2"},
    "gpt-5.5": {"provider": "openai_responses", "model_id": "openai.gpt-5.5",
                "region": "us-east-1"},
    "gpt-oss-120b": {"provider": "bedrock", "model_id": "openai.gpt-oss-120b-1:0",
                     "region": "us-west-2", "omit_temperature": False},
}
