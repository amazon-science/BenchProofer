# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Option types and the plumbing every command shares.

Options are declared once here and reused, so ``--bundle-root`` means the same
thing to every command and its help text is written in one place. Settings are
assembled per invocation and passed down explicitly; no command reads a global.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer

from ..backends.base import Backend
from ..config import Settings, load_settings
from ..core.verdict import Level
from ..errors import ConfigError
from ..llm.base import Provider
from ..llm.record import Recorder
from ..llm.resolve import resolve, reviewer
from ..pipeline.adjudicate import UNWAIVABLE
from ..registries import BACKENDS

__all__ = [
    "AuditModel",
    "BackendOption",
    "BenchmarkArgument",
    "BundleRoot",
    "CacheDir",
    "Concurrency",
    "Extra",
    "Ids",
    "JsonOut",
    "LevelOption",
    "Limit",
    "Model",
    "Offline",
    "ProviderName",
    "Record",
    "backend_for",
    "extras_from",
    "flag",
    "provider_for",
    "reviewer_for",
    "settings_for",
    "waivers_from",
]

BundleRoot = Annotated[
    Path | None,
    typer.Option("--bundle-root", metavar="DIR", help="Where bundles are read and written."),
]
CacheDir = Annotated[
    Path | None,
    typer.Option("--cache-dir", metavar="DIR", help="Where datasets and checkouts are cached."),
]
BackendOption = Annotated[
    str | None,
    typer.Option("--backend", "-b", metavar="NAME", help="Verification backend to use."),
]
ProviderName = Annotated[
    str | None,
    typer.Option("--provider", metavar="NAME", help="Model provider for the drafting stage."),
]
Model = Annotated[
    str | None,
    typer.Option("--model", metavar="ID", help="Provider-specific model identifier."),
]
AuditModel = Annotated[
    str | None,
    typer.Option(
        "--audit-model",
        metavar="ID",
        help="Model that reviews the artifacts. Use a different one from --model.",
    ),
]
Record = Annotated[
    bool,
    typer.Option(
        "--record",
        help="Write a cassette for every model exchange, as the record of what the run asked.",
    ),
]
Offline = Annotated[
    bool,
    typer.Option("--offline", help="Refuse network access and use only cached inputs."),
]
Concurrency = Annotated[
    int | None,
    typer.Option("--concurrency", "-j", metavar="N", min=1, help="Tasks worked on at once."),
]
Limit = Annotated[
    int | None,
    typer.Option("--limit", "-n", metavar="N", min=1, help="Take the first N tasks."),
]
Ids = Annotated[
    list[str] | None,
    typer.Option("--id", metavar="TASK_ID", help="Select one task id; repeatable."),
]
LevelOption = Annotated[
    Level,
    typer.Option(
        "--level",
        help="Evidence required: the artifacts alone, plus the benchmark's own tests, "
        "or plus an independent review.",
    ),
]
Extra = Annotated[
    list[str] | None,
    typer.Option("--extra", metavar="KEY=VALUE", help="Adapter-specific option; repeatable."),
]
JsonOut = Annotated[
    bool, typer.Option("--json", help="Print a JSON document instead of a table.")
]
BenchmarkArgument = Annotated[
    str,
    typer.Argument(metavar="BENCHMARK", help="Benchmark name, from 'catalog benchmarks'."),
]


def flag(value: bool) -> bool | None:
    """Translate a boolean flag into an override.

    A flag that was passed overrides the configuration; one that was left alone
    resolves to None and is dropped, so ``--offline`` can turn hermetic mode on
    without its absence turning a configured hermetic mode off.
    """
    return value or None


def settings_for(**overrides: Any) -> Settings:
    """Resolve settings for one invocation.

    Values given on the command line win over ``BENCHPROOFER_*`` environment
    variables, which win over ``benchproofer.toml``. Options left unset are dropped
    rather than passed as None, so an unspecified flag does not overwrite a
    configured value.
    """
    return load_settings(overrides)


def backend_for(name: str | None) -> Backend:
    """Resolve a backend by name and refuse one whose toolchain is absent.

    A backend locates its executable through the toolchain directory in
    ``benchproofer.toml`` or ``BENCHPROOFER_TOOLCHAIN_DIR``, so refusing here is
    what keeps a run from recording a corpus of undecided verdicts.

    Raises:
        ConfigError: No backend was named, or the named one cannot run here.
        PluginError: The name is not registered.
    """
    if not name:
        raise ConfigError(
            "no backend given; pass --backend NAME "
            f"(registered: {', '.join(BACKENDS.names()) or 'none'})"
        )
    backend = BACKENDS.get(name)
    available = backend.availability()
    if not available:
        hint = f" ({available.hint})" if available.hint else ""
        raise ConfigError(f"backend {name!r} cannot run here: {available.detail}{hint}")
    return backend


def provider_for(settings: Settings, *, record: bool = False) -> Provider:
    """Resolve the model provider used for drafting.

    Raises:
        PluginError: The settings name a provider that is not registered.
    """
    return _recording(resolve(settings), record=record)


def reviewer_for(settings: Settings, *, record: bool = False) -> Provider:
    """Resolve the model provider used for the review stage.

    Configured with ``--audit-model`` when one was given. Reviewing with the model that
    drafted the artifacts is allowed and recorded as a self-review, which the
    ``audit.independence`` gate reports rather than counting as evidence.

    Raises:
        PluginError: As `provider_for`.
    """
    return _recording(reviewer(settings), record=record)


def _recording(provider: Provider, *, record: bool) -> Provider:
    """Wrap a provider so every exchange is written to a cassette."""
    return Recorder(provider) if record else provider


def waivers_from(values: list[str] | None) -> dict[str, str]:
    """Parse repeated ``--waive gate=reason`` options.

    The reason is required: what separates certifying over a gate's objection from
    suppressing it is a record of why, next to the verdict. The gates no reason can cover
    (`pipeline.adjudicate.UNWAIVABLE`) are refused here and again by `adjudicate`, which a
    library caller reaches directly.

    Raises:
        ConfigError: An entry gives no reason, names no gate, or names a gate the central
            claim rests on.
    """
    waivers: dict[str, str] = {}
    for entry in values or []:
        gate, separator, reason = entry.partition("=")
        if not separator or not gate.strip() or not reason.strip():
            raise ConfigError(
                f"--waive expects gate=reason, got {entry!r}; a waiver without a reason "
                "is a gate nobody can tell was overruled"
            )
        if gate.strip() in UNWAIVABLE:
            raise ConfigError(
                f"{gate.strip()} cannot be waived: a certificate over it would say the "
                "implementation satisfies the specification where nothing established "
                f"that it does ({', '.join(UNWAIVABLE)})"
            )
        waivers[gate.strip()] = reason.strip()
    return waivers


def extras_from(values: list[str] | None) -> dict[str, str]:
    """Parse repeated ``--extra key=value`` options.

    Raises:
        ConfigError: An entry is not in ``key=value`` form.
    """
    extras: dict[str, str] = {}
    for entry in values or []:
        key, separator, value = entry.partition("=")
        if not separator or not key.strip():
            raise ConfigError(f"--extra expects key=value, got {entry!r}")
        extras[key.strip()] = value
    return extras
