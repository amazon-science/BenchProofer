# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Lean proof-closure inspection: every `theorem correct_<name>` must be
genuinely closed — `#print axioms` shows only STANDARD_AXIOMS + declared callee
axioms, never `sorryAx`. An elaborating file is not a proved one, so this is
what separates the two. Shared by the verify/gold/hygiene gates."""
from __future__ import annotations

import re

from ..backends.lean import STANDARD_AXIOMS
from .base import Bundle
from ._common import check_bundle_source, no_verdict

_CORRECT_RE = re.compile(r"^\s*theorem\s+(correct_[A-Za-z0-9_']+)", re.MULTILINE)
_AXIOM_DECL_RE = re.compile(r"^\s*axiom\s+([A-Za-z0-9_']+)", re.MULTILINE)
# `'name' depends on axioms: [a, b, c]`  /  `'name' does not depend on any axioms`
_AX_LINE_RE = re.compile(
    r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)")


def correct_theorem_names(src: str, tables) -> list[str]:
    """correct_<name> theorems in the proof region(s); whole-file fallback if
    proof regions are unmarked."""
    from ..markers import parse_regions
    names: list[str] = []
    for lo, hi in parse_regions(src, tables).get("proof"):
        chunk = "\n".join(src.splitlines()[lo:hi - 1])
        names += _CORRECT_RE.findall(chunk)
    if not names:
        names = _CORRECT_RE.findall(src)
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def declared_axiom_names(src: str) -> set[str]:
    """Bundle-declared callee axioms (`axiom <callee>_prop : …`)."""
    return set(_AXIOM_DECL_RE.findall(src))


def check_proof_axioms(bundle: Bundle, src: str, timeout: int) -> tuple[bool, str, dict]:
    """Re-elaborate with `#print axioms` appended per correctness theorem;
    returns (ok, detail, data). Any sorryAx or unexpected axiom = fake or
    incomplete proof => reject.

    `data["no_verdict"]` marks the case where the re-elaboration never reported:
    not-ok, but not because the proof is open. Callers surface that as an error
    so the cell is re-measured rather than sent to be re-authored.
    """
    names = correct_theorem_names(src, bundle.backend.language)
    if not names:
        return False, "no `theorem correct_<name>` found in proof region", {}
    allowed = set(STANDARD_AXIOMS) | declared_axiom_names(src)
    augmented = (src.rstrip() + "\n\n"
                 + "\n".join(f"#print axioms {n}" for n in names) + "\n")
    r = check_bundle_source(bundle, augmented, timeout)
    if no_verdict(r):
        return (False, f"#print axioms reached no verdict at {timeout}s: {r.summary}",
                {"no_verdict": True})
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    if "sorryAx" in out:
        return False, "proof depends on sorryAx (fake/incomplete proof)", {"axioms": "sorryAx"}
    if not r.success:
        return False, f"re-elaboration with #print axioms failed: {r.summary}", {}
    reported: dict[str, list[str]] = {}
    for m in _AX_LINE_RE.finditer(out):
        nm = m.group(1)
        axs = [a.strip() for a in (m.group(2) or "").split(",") if a.strip()]
        reported[nm] = axs
    missing = [n for n in names if n not in reported]
    if missing:
        return False, f"#print axioms produced no line for: {missing}", {"reported": reported}
    bad = {}
    for nm, axs in reported.items():
        extra = [a for a in axs if a not in allowed]
        if extra:
            bad[nm] = extra
    if bad:
        return (False, f"proof(s) depend on non-allowed axioms: {bad} "
                f"(allowed: {sorted(allowed)})", {"reported": reported, "bad": bad})
    return (True, f"{len(names)} correct_* theorem(s) closed, axioms clean",
            {"reported": reported})
