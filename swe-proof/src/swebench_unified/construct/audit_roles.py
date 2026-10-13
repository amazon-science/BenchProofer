# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The audit's role table: which reviewer agent scores which gate, which roles
have an executable oracle, what each one reads, and how each is labelled in the
published record.

Its own module because the derivation, the record composer and the stage driver
all key off this table, and a copy any two of them held privately is how a role
ends up scored under one name and published under another.
"""
from __future__ import annotations

from ..gates.eq import reads as _EQ_READS
from ..gates.panel import SUBGATE_READS as _PANEL_SUBGATE_READS


# Three reviewer AGENTS, run in parallel: spec-too-weak, faithfulness, leakage.
# The spec-too-weak agent's single payload feeds BOTH gate verdicts it informs —
# G-EQ (verify⇏correct via resolve) and the panel's G-PANEL-1 (any verifying
# same-spec impl) — so we don't pay for a redundant fourth agent that does
# identical attack work.
_AUDIT_AGENTS = {"eq": ("G-EQ", "G-PANEL-1"),   # one agent -> two gate keys
                 "panel_2": ("G-PANEL-2",),
                 "panel_3": ("G-PANEL-3",)}
# derivation role used to score each recorded gate key from its agent payload.
_GATE_DERIVE_ROLE = {"G-EQ": "eq", "G-PANEL-1": "panel_1",
                     "G-PANEL-2": "panel_2", "G-PANEL-3": "panel_3"}
# self-report verdicts counted as a pass for the JUDGMENT roles (panel_2/3),
# which have no executable oracle — evidence-gated, not machine-derived.
_JUDGMENT_PASS = {"pass", "faithful", "no-leakage", "sound"}

# What each audit ROLE's verdict depends on, for the same reason the mechanical
# gates declare `reads` (gates/base.py source_digests): a record that cannot be
# checked against the artifact it judged attests only that SOME solution at that
# path was audited at that time, and the audit gates are the ones a spec repair
# most often invalidates. Per role rather than per gate module, because panel_2
# and panel_3 judge the spec view and never read the battery -- digesting it for
# them would report those roles stale whenever only the battery was re-authored.
_ROLE_READS = {_GATE_DERIVE_ROLE[gk]: rd
               for gk, rd in _PANEL_SUBGATE_READS.items()}
_ROLE_READS["eq"] = _EQ_READS
# machine-checked roles: pass/fail derives from re-running the attacks.
_MECHANIZED = {"panel_1", "eq"}
MIN_ATTACKS_DEFAULT = 5
# Per-role wall-clock for the audit stage, overridable with SBU_AUDIT_TIMEOUT.
#
# A mechanized role has to read the bundle, stand up the instance image, author
# MIN_ATTACKS_DEFAULT admissible attacks against the spec, and run each one
# through the verifier and the resolve oracle. A cap below that work does not
# record a slow role: the stage fails closed, so it records `INCONCLUSIVE, 0
# attacks of 0 submitted`, which reads afterwards as "the audit found a hole in
# this spec". Fail-closed is the right posture, but it only reports weakness
# while the cap admits a role that works, and a role killed mid-way throws away
# every attack it had authored and every resolve it had run.
#
# A slow role is bounded by the CALLER's outer cap, which is where it belongs.
# The cap must sit above the work, and the work here is bounded by the resolve
# oracle: an attack costs one container run, so a role that authors ten spends
# most of its wall clock in the harness rather than in the model.
AUDIT_ROLE_TIMEOUT_DEFAULT = 10800


# human label per GATE role — one verdict.md section each, never consolidated,
# so a reader can see which role reached which conclusion on which evidence.
_GATE_ROLE_LABEL = {
    "G-EQ": "G-EQ (refinement fidelity)",
    "G-PANEL-1": "G-PANEL-1 (spec-too-weak)",
    "G-PANEL-2": "G-PANEL-2 (faithfulness)",
    "G-PANEL-3": "G-PANEL-3 (leakage)",
}
# The order the roles are published in, so a run that reaches a SUBSET of them
# cannot reorder the file: `merge_verdict_md` interleaves this run's sections with
# the blocks of roles it never attempted, and without a canonical order the result
# would depend on which roles happened to be scoped.
_ROLE_LABEL_ORDER = [_GATE_ROLE_LABEL[g] for g in
                     ("G-EQ", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")]

# The other gate keys each reviewer run informs, so a publisher can find the one
# entry that kept the run's advisory word. See `recorded_agent_verdict`.
_CO_RECORDED = {gate: tuple(g for g in keys if g != gate)
                for keys in _AUDIT_AGENTS.values() for gate in keys}


def recorded_agent_verdict(gates: dict, gate: str) -> str:
    """The reviewing agent's advisory word for the role `gate` names, or `""`.

    The gate's own entry first, then the entries of the other keys the same
    reviewer run informs. The word is recorded per RUN -- `run_audit_stage` writes
    one payload's `verdict` into the entry of every key that payload scores -- and
    only a key with no mechanical gate module of its own keeps it, because
    `gates._record` REPLACES a gate's blob on every re-gate and carries
    `note`/`model` over but not `agent_verdict`. So a publisher that reads the
    named gate alone drops the `eq` reviewer's verdict on every cell: measured over
    both corpora, 0 of 2959 `G-EQ` entries hold the field and all 2952
    `G-PANEL-1` entries do, from the same payload.
    """
    for g in (gate,) + _CO_RECORDED.get(gate, ()):
        entry = gates.get(g)
        av = entry.get("agent_verdict") if isinstance(entry, dict) else None
        if av:
            return str(av)
    return ""
