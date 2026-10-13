# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Runtime settings.

Every value can be set three ways, in increasing precedence: a ``benchproofer.toml``
file in the working directory, a ``BENCHPROOFER_*`` environment variable, and an
explicit command-line option. Nothing reads a global implicitly: commands resolve
settings once and pass them down.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from platformdirs import user_cache_path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigError
from .util.fsio import load_toml

__all__ = ["Settings", "load_settings", "settings"]

CONFIG_FILENAME = "benchproofer.toml"
ENV_PREFIX = "BENCHPROOFER_"


class Settings(BaseSettings):
    """Resolved configuration for one invocation."""

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, extra="ignore", frozen=True)

    #: Where bundles are written and read.
    bundle_root: Path = Path("bundles")
    #: Where downloaded benchmark rows and repositories are cached.
    cache_dir: Path = Field(default_factory=lambda: user_cache_path("benchproofer"))
    #: Where `scripts/install/*.sh` place external verifier toolchains.
    toolchain_dir: Path = Path(".toolchains")

    #: Registered model provider used by the formalization stage.
    provider: str = "null"
    #: Provider-specific model identifier.
    model: str = ""
    #: Model the review stage uses. A review by the drafting model is recorded as a
    #: self-review (`audit.independence`), so a run at level `audited` sets this.
    audit_model: str = ""
    #: Where `--record` writes what the run asks of its models.
    cassette_dir: Path = Path("cassettes")
    #: Whether the run keeps what it asks of models (`--record`): a request a provider
    #: answers is a cassette in `cassette_dir`, and a session's request -- its system
    #: prompt, prompt, tools and budget -- is written under `cassette_dir/sessions`, named
    #: by the id under which Claude Code keeps the conversation itself.
    record: bool = False
    #: Registered agent session for the stages that read the repository to decide what to
    #: write: the solution's draft, the repair, the review, and proof where its switch below
    #: is on. Empty runs none of them, and then nothing can be drafted, reviewed or repaired.
    #: A session that reaches a model does not run `--offline`; `scripted` reaches none and
    #: answers from a packaged fixture.
    session: str = "claude-code"
    #: Model the session runs on. Empty uses the drafting model, so a run's sessions use
    #: the models it declares rather than whatever the machine's own tool is set to.
    session_model: str = ""

    #: Budget of the session that drafts the solution: its turns, and its time in seconds,
    #: what `verified-swebench` gives one step of its author.
    draft_turns: int = 200
    draft_timeout_s: float = 3600.0
    #: Budget of one repair session: its turns, and its time in seconds. The session
    #: budgets here, `verify_timeout_s` and `oracle_timeout_s` are the ones
    #: `verified-swebench` gives the same steps, so the two are compared on one clock.
    repair_turns: int = 200
    repair_timeout_s: float = 9000.0
    #: Budget of one review session, every auditor's alike: its turns, and its time in seconds.
    review_turns: int = 200
    review_timeout_s: float = 10800.0
    #: Whether a drafted file a prover's checker refused goes to an agent session that
    #: writes its proof, with the specification and the implementation held fixed.
    #: Proof-carrying backends only; needs `session`.
    prove_agent: bool = True
    #: Budget of one proof session: its turns, and its time in seconds.
    prove_turns: int = 200
    prove_timeout_s: float = 3600.0

    #: Per-invocation verifier budget, in seconds.
    verify_timeout_s: int = 300
    #: Per-task oracle budget, in seconds.
    oracle_timeout_s: int = 3600
    #: Budget of one run of a drafted program (`conformance.py`, `axioms.py`) in the
    #: task's environment, in seconds. `conformance.py` draws until a share of it
    #: (`core.differential.DEADLINE_SHARE`) has passed.
    harness_timeout_s: int = 1800
    #: Response budget for one model request, in tokens. A model that reasons before it
    #: answers spends this on both, and a reply that runs out of room costs a round.
    max_output_tokens: int = 32768
    #: Tasks formalized or judged concurrently.
    concurrency: int = 4
    #: Refuse any network access, using only cached and shipped inputs.
    offline: bool = False
    #: Mutants generated per bundle. Each one costs a verifier invocation.
    mutation_limit: int = 16
    #: Inputs `conformance.py` aims to compare, for a benchmark with no figure of
    #: its own; the paper's figure is 100,000. A target, not a floor: it draws
    #: until it reaches this or its share of `harness_timeout_s` is spent, and the number
    #: compared is recorded on the verdict for a reader to weigh.
    conformance_inputs: int = 100_000
    #: The target for named benchmarks, keyed on `Task.benchmark` because DeepSWE arrives
    #: through the general `jsonl` adapter. How many inputs are reachable depends on the
    #: code compared: a pure function over small integers takes 100,000 calls in a second,
    #: code reached through object construction and I/O may take that long for a thousand.
    #: A target the tasks can meet makes a shortfall mean something.
    conformance_inputs_by_benchmark: dict[str, int] = Field(
        default_factory=lambda: {"deepswe": 1_000}
    )
    #: Attacks the review stage asks a reviewer for.
    audit_attacks: int = 5
    #: Attacks a review must have filed and had decided before surviving them counts as
    #: evidence. Equal to `audit_attacks` by default: a review that could not produce what
    #: it was asked for is inconclusive.
    audit_min_attacks: int = 5
    #: Correct implementations, written differently from the shipped one, that the review
    #: stage asks a reviewer for. Attacks show a specification is not too weak; only an
    #: accepted correct implementation shows it is not too strong.
    audit_controls: int = 3
    #: Controls the specification must accept, each shown correct, for the soundness gate to
    #: pass. Below `audit_controls`: a control the checker refuses for a proof the reviewer
    #: could not write still shows where the specification may be too strong.
    audit_min_controls: int = 1
    #: Repairs before giving up on certifying a bundle, each counted whether its session's
    #: work was taken or not; an auditor asked again spends none of it (`docs/gates.md`,
    #: "Where a verdict goes"). Each costs a review and a judgement of the whole bundle; this
    #: decides how much of a corpus certifies, so lower it to survey a benchmark and raise it
    #: to finish one.
    max_repairs: int = 5

    def inputs_for(self, benchmark: str) -> int:
        """How many inputs `conformance.py` is asked to compare for ``benchmark``."""
        return self.conformance_inputs_by_benchmark.get(benchmark, self.conformance_inputs)

    def resolved(self, base: Path | None = None) -> Settings:
        """Return a copy with relative paths anchored at ``base``."""
        root = Path(base or Path.cwd())
        updates: dict[str, Any] = {}
        for field in ("bundle_root", "cache_dir", "toolchain_dir", "cassette_dir"):
            value = getattr(self, field)
            if not value.is_absolute():
                updates[field] = (root / value).resolve()
        return self.model_copy(update=updates) if updates else self


def load_settings(
    overrides: dict[str, Any] | None = None, *, base: Path | None = None
) -> Settings:
    """Build settings from the config file, the environment, and ``overrides``.

    Args:
        overrides: Values from the command line. A key whose value is None was not
            given, so it is dropped rather than used to overwrite anything.
        base: Directory the config file is read from and relative paths are anchored
            at. Defaults to the working directory.
    """
    root = Path(base or Path.cwd())
    # File values reach the model as explicit arguments, which would outrank the
    # environment, so a field the environment sets is dropped from them. Command-line
    # overrides are meant to outrank it.
    from_environment = _environment_fields()
    values = {
        key: value
        for key, value in _from_file(root).items()
        if str(key).lower() not in from_environment
    }
    if overrides:
        values.update({key: value for key, value in overrides.items() if value is not None})
    return Settings(**values).resolved(root)


def _from_file(root: Path) -> dict[str, Any]:
    """Read ``benchproofer.toml``, with or without its table header.

    Raises:
        ConfigError: The file is unreadable, is not TOML, or its ``[benchproofer]``
            section is not a table.
    """
    path = root / CONFIG_FILENAME
    if not path.exists():
        return {}
    try:
        document = load_toml(path)
    except Exception as exc:
        raise ConfigError(f"{path}: {exc}") from exc
    section = document.get("benchproofer", document)
    if not isinstance(section, dict):
        raise ConfigError(f"{path}: [benchproofer] must be a table")
    return dict(section)


def _environment_fields() -> set[str]:
    """Field names the ``BENCHPROOFER_*`` environment currently sets."""
    return {key[len(ENV_PREFIX) :].lower() for key in os.environ if key.startswith(ENV_PREFIX)}


@lru_cache(maxsize=1)
def settings() -> Settings:
    """Process-wide settings for callers that do not thread them explicitly."""
    return load_settings()
