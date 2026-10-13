# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-EQ — agentic refinement-fidelity attack (A legs; R/I pre-cleared by
G-CONF). Reads the verdict recorded in meta.json gates.G-EQ by the P2 audit
stage; none recorded => explicit skip. Running the agent is construct-mode
work (_audit.run_audit), never done here."""
from __future__ import annotations

from .base import Bundle, GateResult
from ._audit import recorded_verdict

name = "G-EQ"
applies_to = ("nagini", "velvet", "lean", "ears")
needs_docker = False
agentic = True
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution", "properties")


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    r = recorded_verdict(bundle, name)
    if r is not None:
        return r
    return GateResult(name, "skip",
                      "no recorded G-EQ verdict in meta.json (P2 audit not run)")
