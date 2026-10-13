# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Is the plugin surface installed and coherent.

These two cases are the cheapest useful thing the suite does. They need nothing from
the machine, so they run everywhere, and they catch the failure that would otherwise
make every later case mysterious: a component that is declared in packaging metadata
but does not import, or a required gate that nothing provides.
"""

from __future__ import annotations

from ...core.verdict import Level
from ...pipeline.adjudicate import (
    GATE_ORDER,
    ORACLE_REQUIRED,
    STATIC_REQUIRED,
    required_gates,
)
from ...registries import BACKENDS, BENCHMARKS, GATES, ORACLES, PROVIDERS
from ..model import Case, Context, Observation, check, equals

__all__ = ["CASES"]

_GROUPS = (
    ("backends", BACKENDS),
    ("benchmarks", BENCHMARKS),
    ("oracles", ORACLES),
    ("gates", GATES),
    ("providers", PROVIDERS),
)


def entry_points(context: Context) -> list[Observation]:
    """Every declared component imports, and answers to the name it is filed under."""
    observations: list[Observation] = []
    for group, registry in _GROUPS:
        declared = registry.names()
        check(declared, f"the {group} registry is empty; is benchproofer installed?")

        loaded = registry.load_all(skip_broken=False)
        equals(sorted(loaded), sorted(declared), f"{group}: names() against load_all()")
        for name, component in loaded.items():
            identity = getattr(component, "id", None) or getattr(component, "name", None)
            equals(identity, name, f"{group}: the component behind {name!r} names itself")
        observations.append(
            Observation(group, f"{len(loaded)} loaded: {', '.join(sorted(loaded))}")
        )
    return observations


def gate_coverage(context: Context) -> list[Observation]:
    """The required gates exist, and the evidence levels line up with them.

    A gate an installed plugin adds is not a defect: it is judged and reported
    without changing what certification means. So this case asks that nothing the
    tool relies on is absent, not that nothing else is present.
    """
    gates = GATES.load_all(skip_broken=False)
    registered = set(gates)

    unordered = sorted(set(GATE_ORDER) - registered)
    check(not unordered, f"gate(s) in the execution order are not registered: {unordered}")
    missing = sorted(set(ORACLE_REQUIRED) - registered)
    check(not missing, f"required gate(s) are not registered: {', '.join(missing)}")
    check(
        set(STATIC_REQUIRED) <= set(ORACLE_REQUIRED),
        "the static requirement is not a subset of the oracle requirement, so raising "
        "the evidence level could certify a bundle that a cheaper run rejected",
    )

    oracle_level = {gate_id for gate_id, gate in gates.items() if gate.level is Level.ORACLE}
    equals(
        sorted(oracle_level & set(ORACLE_REQUIRED)),
        sorted(set(ORACLE_REQUIRED) - set(STATIC_REQUIRED)),
        "required gates declaring level=oracle against the gates the oracle level adds",
    )

    undocumented = sorted(gate_id for gate_id, gate in gates.items() if not gate.rationale)
    check(not undocumented, f"gate(s) state no rationale: {', '.join(undocumented)}")

    added = sorted(registered - set(GATE_ORDER))
    return [
        Observation("static", f"{len(required_gates(Level.STATIC))} gates required"),
        Observation("oracle", f"{len(required_gates(Level.ORACLE))} gates required"),
        Observation("oracle-level gates", ", ".join(sorted(oracle_level))),
        Observation("beyond the built-ins", ", ".join(added) or "none registered"),
    ]


CASES: tuple[Case, ...] = (
    Case(
        id="registry.entry_points",
        summary="every declared plugin imports and reports its own name",
        procedure=entry_points,
    ),
    Case(
        id="registry.gate_coverage",
        summary="the required gates are registered and their levels agree",
        procedure=gate_coverage,
    ),
)
