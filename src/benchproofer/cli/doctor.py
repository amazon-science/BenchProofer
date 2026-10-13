# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""``benchproofer doctor``: what works here, and what to install next.

The tool is deliberately usable with parts of it missing: a machine with no Dafny
can still ingest tasks and judge Python bundles. This command reports which parts
are ready rather than failing on the first absence, and every unavailable component
carries the command that installs it.
"""

from __future__ import annotations

from typing import Annotated, Any

import typer

from ..core.provenance import environment_report
from . import catalog
from .display import availability_cells, emit_json, grid, note, problem, stdout
from .options import BundleRoot, JsonOut, Model, ProviderName, settings_for

__all__ = ["doctor"]

Strict = Annotated[
    bool,
    typer.Option("--strict", help="Exit non-zero unless a backend and the provider are ready."),
]


def doctor(
    bundle_root: BundleRoot = None,
    provider: ProviderName = None,
    model: Model = None,
    json_out: JsonOut = False,
    strict: Strict = False,
) -> None:
    """Report the environment, the resolved settings, and which components are ready.

    ``--provider`` and ``--model`` report on the run you are about to make rather
    than on the configured default, which matters because a provider's credential
    can follow from the model id.
    """
    settings = settings_for(bundle_root=bundle_root, provider=provider, model=model)
    sections = {
        "backends": catalog.backends(),
        "oracles": catalog.oracles(),
        "providers": catalog.providers(settings.model),
    }
    ready_backends = [row["name"] for row, ok in sections["backends"] if ok]
    provider_ready = any(
        row["name"] == settings.provider and ok for row, ok in sections["providers"]
    )

    if json_out:
        described = {
            name: [_as_json(entry) for entry in rows] for name, rows in sections.items()
        }
        emit_json(
            {
                "environment": environment_report(),
                "settings": settings.model_dump(mode="json"),
                **described,
                "ready_backends": ready_backends,
                "provider_ready": provider_ready,
            }
        )
    else:
        _render(settings.model_dump(mode="json"), sections)
        note("")
        if ready_backends:
            note(f"Backends ready: {', '.join(ready_backends)}")
        else:
            note("No verification backend is installed; see the hints above.")
        state = "configured." if provider_ready else "not usable yet."
        note(f"Provider {settings.provider!r} is {state}")

    if strict and not (ready_backends and provider_ready):
        problem("strict mode: a usable backend and provider are both required")
        raise typer.Exit(code=1)


def _as_json(entry: catalog.Entry) -> dict[str, Any]:
    """Flatten one catalog entry, readiness included, for ``--json``."""
    row, availability = entry
    return {
        **row,
        "available": bool(availability),
        "version": availability.version,
        "detail": availability.detail,
        "hint": availability.hint,
    }


def _render(settings: dict[str, Any], sections: dict[str, list[catalog.Entry]]) -> None:
    """Print the environment, the settings, and one table per registry."""
    environment = environment_report()
    facts = grid("", "", title="environment")
    for key in ("tool_version", "python", "platform", "judge_digest"):
        value = str(environment.get(key, ""))
        facts.add_row(key, value[:16] if key == "judge_digest" else value)
    stdout.print(facts)

    stdout.print()
    # All of them, in the order they are declared: a setting resolved from a file or
    # the environment rather than from a flag is invisible anywhere else.
    resolved = grid("setting", "value", title="settings in effect")
    for key, value in settings.items():
        resolved.add_row(key, str(value))
    stdout.print(resolved)

    for name, rows in sections.items():
        stdout.print()
        table = grid("name", "summary", "status", "detail", title=name)
        for row, availability in rows:
            state, detail = availability_cells(availability)
            table.add_row(row["name"], row["summary"], state, detail)
        stdout.print(table)
