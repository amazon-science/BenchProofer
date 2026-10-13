# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Velvet backend: Lean 4 + Velvet/Loom (proofs discharged automatically by
loom_solve/SMT), checked on the host against the shared lean_shared workspace
(toolchain v4.24.0) via scripts/lean_verify.sh."""
from __future__ import annotations

from pathlib import Path

from ..paths import SCRIPTS_ROOT
from ..verify import VerifyResult, run_verify_script
from .base import Backend, LanguageTables, ShadowSpec

VERIFY_SCRIPT = SCRIPTS_ROOT / "lean_verify.sh"


class VelvetBackend(Backend):
    name = "velvet"
    language = LanguageTables(
        flavor="lean",
        solution_filename="Solution.lean",
        comment_line="--",
        region_names=("axioms", "pure", "pre-conditions", "post-conditions",
                      "invariants", "impl"),
        import_allowlist=("Velvet", "Mathlib", "Std", "Lean", "Init",
                          "Batteries", "Aesop"),
        banned_tokens=("sorry", "admit", "Classical.choice", "unsafe ",
                       "extern", "native_decide"),
    )

    def check(self, path: Path, timeout: int = 300) -> VerifyResult:
        return run_verify_script(VERIFY_SCRIPT, path, timeout)

    def conf_shadow(self, bundle_dir: Path) -> ShadowSpec | None:
        """Lean is non-executable here: the shadow is the agent-written
        conformance_check.py transliteration — provenance "transliterated",
        the least-trustworthy link (docs/adding_a_backend.md §1)."""
        script = bundle_dir / "conformance_check.py"
        if not script.exists():
            return None
        return ShadowSpec(provenance="transliterated", script=script)

    def verifier_tool_name(self) -> str:
        return "velvet_verify"
