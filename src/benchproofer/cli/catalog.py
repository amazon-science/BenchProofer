# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer catalog``: what this installation can do.

Everything listed here is discovered through entry points, so a component added by
another package appears in this output with no change to the tool.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

import typer

from ..core.plugin import Availability
from ..llm.base import ProviderConfig
from ..registries import BACKENDS, BENCHMARKS, GATES, ORACLES, PROVIDERS, SESSIONS
from .display import availability_cells, emit_json, grid, note, stdout
from .options import JsonOut

__all__ = [
    "Entry",
    "Kind",
    "backends",
    "benchmarks",
    "catalog",
    "gates",
    "oracles",
    "providers",
]

#: One catalog line: the machine-readable row, and how ready that component is.
Entry = tuple[dict[str, Any], Availability]


class Kind(str, Enum):
    """Which registry to list."""

    ALL = "all"
    BENCHMARKS = "benchmarks"
    BACKENDS = "backends"
    ORACLES = "oracles"
    GATES = "gates"
    PROVIDERS = "providers"
    SESSIONS = "sessions"

    def __str__(self) -> str:
        return self.value


KindArgument = Annotated[Kind, typer.Argument(help="Which registry to list.")]


def catalog(kind: KindArgument = Kind.ALL, json_out: JsonOut = False) -> None:
    """List the benchmarks, backends, oracles, gates, providers, and sessions here."""
    sections = {
        Kind.BENCHMARKS: benchmarks,
        Kind.BACKENDS: backends,
        Kind.ORACLES: oracles,
        Kind.GATES: gates,
        Kind.PROVIDERS: providers,
        Kind.SESSIONS: sessions,
    }
    wanted = list(sections) if kind is Kind.ALL else [kind]

    if json_out:
        emit_json({str(name): [row for row, _ in sections[name]()] for name in wanted})
        return

    for index, name in enumerate(wanted):
        if index:
            stdout.print()
        _render(name, sections[name]())


def benchmarks() -> list[Entry]:
    """Describe every registered benchmark adapter."""
    entries: list[Entry] = []
    for name, adapter in sorted(BENCHMARKS.load_all().items()):
        info = adapter.info()
        entries.append(
            (
                {
                    "name": name,
                    "title": info.title,
                    "tasks": info.size,
                    "oracle": info.oracle,
                    "license": info.license,
                    "network": info.remote,
                    "url": info.url,
                    "summary": info.summary,
                },
                adapter.availability(),
            )
        )
    return entries


def backends() -> list[Entry]:
    """Describe every registered verification backend."""
    entries: list[Entry] = []
    for name, backend in sorted(BACKENDS.load_all().items()):
        entries.append(
            (
                {
                    "name": name,
                    "language": backend.language,
                    "answer": str(backend.kind),
                    "extension": backend.extension,
                    # Seconds this checker spends before it reasons about anything, which
                    # is what `verify_timeout_s` gets added to rather than taken out of.
                    "startup_s": backend.startup_s,
                    "summary": backend.summary,
                },
                backend.availability(),
            )
        )
    return entries


def oracles() -> list[Entry]:
    """Describe every registered correctness oracle."""
    return [
        (
            {
                "name": name,
                "summary": oracle.summary,
                "needs_docker": oracle.needs_docker,
            },
            oracle.availability(),
        )
        for name, oracle in sorted(ORACLES.load_all().items())
    ]


def providers(model: str = "") -> list[Entry]:
    """Describe every registered model provider.

    Whether a provider is usable can depend on which model is asked of it: an
    Anthropic model id decides whether the credential that matters is an API key or
    an AWS region. The model under consideration is therefore passed in rather than
    left to each provider's default.
    """
    entries: list[Entry] = []
    for name, provider in sorted(PROVIDERS.load_all().items()):
        provider.configure(ProviderConfig(model=model))
        entries.append(
            (
                {
                    "name": name,
                    "summary": provider.summary,
                    "deterministic": provider.deterministic,
                },
                provider.availability(),
            )
        )
    return entries


def sessions(model: str = "") -> list[Entry]:
    """Describe every registered agent session.

    Listed apart from the providers because what they offer is not the same thing. A
    provider continues a conversation and each exchange can be recorded; a session reads
    the repository and decides what to read next, which no cassette can reproduce. A
    run that has providers and no session can judge a bundle but cannot draft one.
    """
    entries: list[Entry] = []
    for name, session in sorted(SESSIONS.load_all().items()):
        session.model = model
        entries.append(({"name": name, "summary": session.summary}, session.availability()))
    return entries


def gates() -> list[Entry]:
    """Describe every registered gate, in the order adjudication runs them."""
    from ..pipeline.adjudicate import AUDITED_REQUIRED, GATE_ORDER

    order = {gate_id: index for index, gate_id in enumerate(GATE_ORDER)}
    ordered = sorted(
        GATES.load_all().values(), key=lambda gate: (order.get(gate.id, len(order)), gate.id)
    )
    return [
        (
            {
                "id": gate.id,
                "title": gate.title,
                "level": str(gate.level),
                # Whether certification depends on this gate at the level it runs at.
                # The required sets are nested, so the top of the ladder holds them all.
                "required": gate.id in AUDITED_REQUIRED,
                "rationale": gate.rationale,
            },
            Availability.ok(),
        )
        for gate in ordered
    ]


def _render(kind: Kind, entries: list[Entry]) -> None:
    """Print one section as a table."""
    if not entries:
        note(f"[bold]{kind}[/bold]: none registered")
        return

    if kind is Kind.GATES:
        table = grid("gate", "level", "required", "what it catches", title=str(kind))
        for row, _ in entries:
            table.add_row(
                row["id"],
                row["level"],
                "yes" if row["required"] else "no",
                row["rationale"] or row["title"],
            )
    elif kind is Kind.BENCHMARKS:
        table = grid(
            "benchmark", "tasks", "oracle", "license", "status", "detail", title=str(kind)
        )
        for row, availability in entries:
            state, detail = availability_cells(availability)
            table.add_row(
                row["name"],
                "?" if row["tasks"] is None else str(row["tasks"]),
                row["oracle"],
                row["license"] or "-",
                state,
                detail,
            )
    elif kind is Kind.BACKENDS:
        table = grid("backend", "language", "kind", "status", "detail", title=str(kind))
        for row, availability in entries:
            state, detail = availability_cells(availability)
            table.add_row(row["name"], row["language"], row["answer"], state, detail)
    else:
        table = grid("name", "summary", "status", "detail", title=str(kind))
        for row, availability in entries:
            state, detail = availability_cells(availability)
            table.add_row(row["name"], row["summary"], state, detail)

    stdout.print(table)
