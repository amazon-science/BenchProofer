# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Lean backend: vanilla Lean 4 + Mathlib with AGENT-WRITTEN proofs.

`check()` is a pure mechanical judgment (exit 3 = sorry-only, a valid
intermediate state during construction); the proof-writing agent lives in
swebench_unified.prove, construction-only (docs/architecture.md §3). Shares the
lean_shared workspace and lean_verify.sh with velvet — the backends differ in
Solution.lean content and hygiene rules, not in how a file is checked.
"""
from __future__ import annotations

from pathlib import Path

from ..paths import SCRIPTS_ROOT
from ..verify import VerifyResult, run_verify_script
from .base import Backend, LanguageTables, ShadowSpec

VERIFY_SCRIPT = SCRIPTS_ROOT / "lean_verify.sh"

# Axioms any proof may depend on; anything else must be declared in the
# bundle's axioms region (verify gate's #print axioms pass).
STANDARD_AXIOMS = ("propext", "Classical.choice", "Quot.sound")


class LeanBackend(Backend):
    name = "lean"
    language = LanguageTables(
        flavor="lean",
        solution_filename="Solution.lean",
        comment_line="--",
        region_names=("axioms", "pure", "pre-conditions", "post-conditions",
                      "impl", "proof"),
        import_allowlist=("Mathlib", "Std", "Lean", "Init", "Batteries", "Aesop"),
        # Unlike velvet, `Classical.choice` is allowed: Mathlib proofs
        # legitimately depend on it; tracked via the standard-axioms check.
        banned_tokens=("sorry", "admit", "sorryAx", "unsafe ", "extern",
                       "native_decide"),
    )

    def check(self, path: Path, timeout: int = 300) -> VerifyResult:
        return run_verify_script(VERIFY_SCRIPT, path, timeout)

    def conf_shadow(self, bundle_dir: Path) -> ShadowSpec | None:
        script = bundle_dir / "conformance_check.py"
        if not script.exists():
            return None
        return ShadowSpec(provenance="transliterated", script=script)

    def verifier_tool_name(self) -> str:
        return "lean_verify"
