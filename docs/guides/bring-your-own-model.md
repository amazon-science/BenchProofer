# Bring your own model

A provider is used by three stages: drafting (`formalize`), reviewing (`audit`) and
repairing (`repair`). No gate calls a language model. Gates read files, run checkers and
read the auditors' recorded judgments, so a corpus can be judged again by anyone, with no
credential at all.

That is worth knowing before you pick one. Switching language models changes how many
bundles get built and how good they are. It cannot change what "certified" means, and it
cannot make a weak specification pass.

## What ships

```bash
benchproofer catalog providers
```

| provider | is |
| --- | --- |
| `anthropic` | Claude models through the Anthropic API or Amazon Bedrock |
| `openai` | any endpoint that speaks the OpenAI chat-completions protocol |
| `null` | the default: refuses every request, so an unconfigured run says so |
| `scripted` | the smoke suite's fixture author; not for real runs |

`null` being the default is deliberate. A run that was never given a language model
reports that nothing could be drafted rather than quietly producing an artifact from
nothing.

## A hosted API

```bash
export ANTHROPIC_API_KEY=...
benchproofer formalize humaneval --backend dafny --provider anthropic --model claude-opus-5
```

```bash
export OPENAI_API_KEY=...
benchproofer formalize humaneval --backend dafny --provider openai --model gpt-4.1
```

Credentials are read from the environment by the provider itself, never from settings, so
a key does not pass through an object that gets written into a report. `benchproofer
doctor` reports which providers are configured without printing any of them.

For Bedrock, use a profile id such as `us.anthropic.claude-opus-5` and set `AWS_REGION`.
The `anthropic` provider picks the endpoint from the shape of the model id, so the same
command works on a laptop with an API key and on a cluster with Bedrock credentials.

## A self-hosted model

Anything that speaks the OpenAI chat-completions protocol needs no plugin. That covers
vLLM, llama.cpp, Ollama, and most hosting providers:

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=unused
benchproofer formalize humaneval --backend dafny --provider openai --model my-local-model
```

With `OPENAI_BASE_URL` set to something other than the OpenAI API, the provider reports
itself as available even with no key, because self-hosted servers commonly accept any key
or none.

## Record a run

A language model's output is not reproducible, and an agent session's turns depend on
what the filesystem said as it ran, so a run is not repeated by running it again.
`--record` keeps what the run asked:

```bash
benchproofer formalize humaneval --backend dafny --provider anthropic --record
```

Every exchange is written to a cassette keyed by a digest of the request: the system
prompt, the messages, the model id, `max_tokens`, and the temperature, beside the reply.
What each agent session was asked is written under `<cassette dir>/sessions/`, named by
the session id Claude Code keeps its transcript under. With the bundles, the cassettes and
the transcripts are what reproduces a run: judging a bundle is deterministic, so anyone can
derive its verdicts again with no key at all. Cassettes live in `cassette_dir`
(`cassettes/` by default) and are small enough to commit next to a paper.

## Writing a provider

Write one when your endpoint speaks neither protocol: a local process, a queue, a
gateway with its own auth. One method is required.

```python
import os
from typing import ClassVar

from benchproofer.core.plugin import Availability
from benchproofer.errors import ProviderError
from benchproofer.llm.base import Completion, Message, Provider

ENDPOINT = "https://gateway.internal/v1/complete"


class MyProvider(Provider):
    """Talk to whatever we run in-house."""

    name: ClassVar[str] = "in-house"
    summary: ClassVar[str] = "the in-house gateway"
    deterministic: ClassVar[bool] = False

    def availability(self) -> Availability:
        if not os.environ.get("INHOUSE_TOKEN"):
            return Availability.missing(
                "INHOUSE_TOKEN is not set", hint="export INHOUSE_TOKEN=..."
            )
        return Availability.ok(detail=ENDPOINT)

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        if self.config.offline:
            raise ProviderError("this run is offline, so the in-house provider cannot be used")
        if not self.config.model:
            raise ProviderError("the in-house provider needs a model id; pass --model")

        reply = call_the_gateway(...)
        return Completion(
            text=reply["text"],
            model=reply.get("model", self.config.model),
            stop_reason=reply.get("stop_reason", ""),
            input_tokens=reply.get("input_tokens", 0),
            output_tokens=reply.get("output_tokens", 0),
        )
```

What the pipeline expects of you:

* **Raise `ProviderError`, never return an empty completion.** A failed request that
  returns empty text becomes an unusable reply, which is retried and then reported as a
  drafting failure. A raised error is reported as what it was. If the very first request
  fails, `formalize` stops without writing a bundle; a failure later on is noted in the
  drafting log (`notes.md`) and the artifacts already drafted are kept.
* **Honor `self.config.offline`.** An offline run must not reach the network, and saying
  so is more useful than a connection error.
* **Report token counts if you have them.** They are what the run's cost accounting is
  built from.
* **Pass the endpoint's `stop_reason` through.** `max_tokens` and `length` tell the
  session that a reply ran out of room rather than that it was unreadable, which is the
  difference between a request the user fixes by raising `max_output_tokens` and one they
  cannot explain. A language model that reasons before it replies can spend the whole
  budget on the reasoning and return no text at all.
* **Set `deterministic` honestly.** Only `null` claims it. Reports read it when they
  describe how repeatable a run is.

Configuration arrives through `configure(config)` rather than `__init__`, because the
registry instantiates a provider with no arguments. `ProviderConfig` carries the model
id, the cassette directory, the offline flag, the retry count, and the timeout. It
carries no credentials, on purpose: read yours from the environment.

Retries are yours to implement. The `openai` provider retries on 408, 409, 429, and 5xx
with exponential backoff, up to `config.max_retries`, and gives up with a
`ProviderError` naming the last failure; it is a reasonable template.

## Register it

```toml
[project.entry-points."benchproofer.providers"]
in-house = "my_package.provider:MyProvider"
```

```bash
pip install -e .
benchproofer doctor
benchproofer formalize humaneval --backend dafny --provider in-house --model whatever --record
```

Record the runs you publish, so a reader can see what each stage was asked and what it replied.

## Checklist

* `availability()` names the missing environment variable and the command that sets it.
* Failures raise `ProviderError` instead of returning empty text.
* `offline` is honored.
* Credentials come from the environment, not from settings.
* A recorded run writes one cassette per request: `--record`, then look in
  `cassette_dir`.
