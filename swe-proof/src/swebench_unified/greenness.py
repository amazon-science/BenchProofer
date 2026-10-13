# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""THE definition of "this bundle is fully green", and of which gate is failing.

Every consumer reads the same predicate: the release gate's batch picker
(`scripts/green_check.py`), the review site's badges and boards
(`viz/backend/data.py`), and the repair drivers that decide whether a cell still
needs work. Two implementations of it, however carefully mirrored, disagree
eventually -- and they disagree about exactly the cells being repaired, where one
says "already done" and the other keeps spending. So the predicate lives here and
nothing re-derives it.

STRICT, in three senses:

  * every mechanical gate AND `G-EQ` must be RECORDED in meta.json, with status
    pass / skip / relaxed. A MISSING stamp is not green: unrecorded work is not
    vouched for.
  * `G-CONF` and `G-PBT` must be REAL verdicts. Three skips mean "not constructed
    yet" rather than "survived": the benchmark-level "does not support G-CONF"
    placeholder from before the gate was wired, a `conf_missing_script` skip (no
    conformance_check.py in the bundle), and a `pbt_missing_manifest` skip (no
    properties.py battery). An intentional per-bundle skip -- G-MUT on an
    assignment-only spec, an empty battery on a blocked bundle -- still counts.
  * the agentic audit must be complete: all three `G-PANEL-<n>` roles, or the
    legacy collective `G-PANEL` rollup for a bundle stamped before the split.

The gate list itself is read off the registry (`gates.STATIC_GATES` /
`DOCKER_GATES` / `AUDIT_GATES`), so a gate added there is required here without an
edit, which is the property that makes a new gate impossible to forget.

Everything here reads a `meta.json` "gates" mapping and nothing else -- never a log
line, never an agent's self-report.
"""
from __future__ import annotations

from collections.abc import Iterable

from .gates import AUDIT_GATES, DOCKER_GATES, STATIC_GATES
from .gates.panel import ROLES as _PANEL_ROLES

# statuses that count toward green; 'relaxed' is a recorded, justified allowance
GREEN_OK = ("pass", "skip", "relaxed")
# genuine negative verdicts: any of these anywhere means the bundle is failing.
# 'n/a' and a gate-level 'blocked' are skip-like; 'pending*' are in-flight markers.
GATE_BAD = ("fail", "error", "unsatisfiable", "would-fail")

PANEL_ROLES = tuple(f"G-PANEL-{i}" for i in sorted(_PANEL_ROLES))
# canonical execution order, for display and for stable reason strings
GATE_ORDER = (*STATIC_GATES, *DOCKER_GATES, *AUDIT_GATES)
# the gates every green bundle must carry a real verdict for, panel excluded
# (its roles are checked separately, since a legacy rollup satisfies them)
REQUIRED_GATES = (*STATIC_GATES, *DOCKER_GATES, "G-EQ")


def _rec(gates: dict, key: str) -> dict:
    v = gates.get(key)
    return v if isinstance(v, dict) else {}


def _data(rec: dict) -> dict:
    """A gate record's `data` blob as a mapping.

    A record damaged into another shape -- `data` written as a list, a string, a
    number -- carries none of the flags read below, and answering "not green" for
    that one cell is the whole cost. Reading it as a mapping regardless raises
    instead, which on the review site is a 500 for the page and on a corpus sweep
    is every other cell's verdict lost with it.
    """
    d = rec.get("data")
    return d if isinstance(d, dict) else {}


def conf_check_ran(gates: dict) -> bool:
    """Whether the conformance check was actually performed on THIS bundle.

    Three stamps mean it was not, and all three are recorded as skips because a
    failure would conflate them with a real disagreement: `conf_missing_script`
    (the bundle has no conformance_check.py), `docker_oracle_unavailable` (no
    oracle on the host that ran the gate), and the pre-wiring benchmark-level
    "does not support G-CONF" placeholder. G-CONF is required on every backend, so
    the script has to be constructed rather than skipped around.

    Separate from `conf_is_real_verdict` because the two questions differ on a
    FAIL: greenness needs a verdict that is OK, while a driver that authors a
    missing conformance script must ask only whether the check ran at all, or it
    overwrites a script the gate has already refuted.
    """
    v = _rec(gates, "G-CONF")
    if not v:                     # no record, or one damaged out of shape
        return False
    data = _data(v)
    if data.get("docker_oracle_unavailable") or data.get("conf_missing_script"):
        return False
    return "does not support G-CONF" not in (v.get("detail") or "")


def conf_is_real_verdict(gates: dict) -> bool:
    """Whether an OK `G-CONF` stamp is a judgment about THIS bundle."""
    return (_rec(gates, "G-CONF").get("status") in GREEN_OK
            and conf_check_ran(gates))


def _pbt_is_real_verdict(gates: dict) -> bool:
    """Same convention for `G-PBT`: a missing-manifest skip is "battery not built
    yet" (lean and velvet predate the gate), not "the spec survived falsification".
    """
    v = _rec(gates, "G-PBT")
    if v.get("status") not in GREEN_OK:
        return False
    return not _data(v).get("pbt_missing_manifest")


def failing_reasons(gates: dict) -> list[str]:
    """Why this bundle is not green, as `<gate>=<what>` strings; empty means green.

    The reason strings are the human-facing half of the predicate and are read by
    triage sweeps, so they name the gate first and the cause second.
    """
    if not gates:
        return ["no gates recorded"]
    bad: list[str] = []
    for gk in REQUIRED_GATES:
        st = _rec(gates, gk).get("status")
        if st is None:
            bad.append(f"{gk}=MISSING")
        elif st not in GREEN_OK:
            bad.append(f"{gk}={st}")
    if _rec(gates, "G-CONF").get("status") in GREEN_OK and not conf_is_real_verdict(gates):
        bad.append("G-CONF=placeholder-skip")
    if _rec(gates, "G-PBT").get("status") in GREEN_OK and not _pbt_is_real_verdict(gates):
        bad.append("G-PBT=missing-manifest")
    roles = [_rec(gates, r).get("status") for r in PANEL_ROLES]
    if all(s is not None for s in roles):
        bad += [f"{r}={s}" for r, s in zip(PANEL_ROLES, roles) if s not in GREEN_OK]
    else:
        p = _rec(gates, "G-PANEL").get("status")
        if p is None:
            bad.append("G-PANEL=MISSING")
        elif p not in GREEN_OK:
            bad.append(f"G-PANEL={p}")
    return bad


def is_green(gates: dict) -> bool:
    """Fully green: nothing missing, nothing failing, no placeholder verdict."""
    return not failing_reasons(gates)


def failing_gates(gates: dict, order: Iterable[str] | None = None) -> list[str]:
    """Gates carrying a genuine NEGATIVE verdict, in display order.

    Narrower than `failing_reasons`: a missing stamp is not listed here, because
    this answers "which gate said no" (badges, worklists) rather than "may this
    bundle be called green".
    """
    keys = list(order or GATE_ORDER)
    keys = [k for k in keys if k != "G-PANEL"] + [*PANEL_ROLES, "G-PANEL"]
    return [k for k in keys if _rec(gates, k).get("status") in GATE_BAD]
