# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-LEAK — spec-view anti-leakage screen (mechanical half). A documented
relaxation (RELAXED_LEAKAGE.md + `relaxed_leakage` meta flag, or recorded
status "relaxed") is a SEMANTIC leak the lexical screen usually misses, so
honor it even when the screen passes — else the recorded relaxation would be
overwritten by a misleading "spec view clean" pass."""
from __future__ import annotations

from .. import leakage
from .base import Bundle, GateResult, load_frozen_row

name = "G-LEAK"
applies_to = ("nagini", "velvet", "lean", "ears")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution", "relaxed_leakage_doc")


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    row = load_frozen_row(bundle.instance_id)
    if row is None:
        return GateResult(name, "error",
                          f"{bundle.instance_id} not in frozen dataset")
    # test_patch is consulted by the ears flavor only (its screen is test-leak
    # oriented — the whole requirements.md is the spec view).
    rep = leakage.screen(bundle.solution_src(), bundle.backend.language,
                         row["patch"], row.get("problem_statement", ""),
                         test_patch=row.get("test_patch", "") or "")
    meta = bundle.meta()
    meta_status = meta.get("gates", {}).get("G-LEAK", {}).get("status")
    relaxed = (
        meta_status == "relaxed"
        or (meta.get("relaxed_leakage") is True
            and (bundle.root / "RELAXED_LEAKAGE.md").exists())
    )
    if relaxed:
        doc = bundle.root / "RELAXED_LEAKAGE.md"
        directed = leakage.reviewer_directed(
            doc.read_text(errors="replace") if doc.is_file() else "")
        if directed:
            # Not a pass with a caveat: the relaxation IS the argument in this
            # file, and an argument that also tells the leakage panel what to
            # record has no independent verdict behind it to relax on.
            return GateResult(
                name, "fail",
                "RELAXED_LEAKAGE.md instructs the panel that reviews it "
                f"({', '.join(directed)}); state the mismatch and let the "
                "panel reach its own verdict",
                {"failures": rep.hard_failures, "reviewer_directed": directed})
        detail = " || ".join(rep.hard_failures) if rep.hard_failures else \
            "semantic leak of gold discriminator; unavoidable for a faithful spec"
        return GateResult(name, "relaxed",
                          "RELAXED per RELAXED_LEAKAGE.md: " + detail,
                          {"failures": rep.hard_failures})
    if rep.passed:
        return GateResult(name, "pass", "spec view clean", {"failures": []})
    return GateResult(name, "fail", "FAILURES: " + " || ".join(rep.hard_failures),
                      {"failures": rep.hard_failures})
