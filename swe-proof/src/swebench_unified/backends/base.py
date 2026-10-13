# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The Backend interface: everything backend-specific hangs off one object so
gates and modes stay generic (docs/adding_a_backend.md §1).

Constraints: gates only ever call `check()` -- a deterministic, read-only
judgment of the committed bundle (the lean proof *search* lives in
swebench_unified.prove, construction-only) -- and should take the narrowest
capability they need; per-backend `if` chains in a gate signal this interface
needs splitting.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..verify import VerifyResult


@dataclass(frozen=True)
class LanguageTables:
    """Lexing + hygiene tables for a backend's spec language. Consumed by
    markers/mutation/leakage (dispatching on `flavor`) and the hygiene gate
    (per-backend allowlists)."""
    # Three flavors over four backends: velvet and lean share the "lean" flavor,
    # so a flavor is a spec LANGUAGE, not a backend. ears is prose, which is why
    # it has no comment syntax.
    flavor: str                # "python" | "lean" | "ears"
    solution_filename: str     # "model.py" | "Solution.lean" | "requirements.md"
    comment_line: str          # "#" | "--" | "" (ears)
    region_names: tuple[str, ...]
    import_allowlist: tuple[str, ...]
    banned_tokens: tuple[str, ...]


@dataclass(frozen=True)
class ShadowSpec:
    """How G-CONF obtains the executable shadow of the formal impl
    (docs/adding_a_backend.md §1): nagini runs the impl region directly
    ("direct"); velvet/lean use the agent-written conformance_check.py
    transliteration ("transliterated" -- the least-trustworthy link; the gate
    records this provenance)."""
    provenance: str                        # "direct" | "transliterated"
    script: Path                           # in-container entry point


class Backend(ABC):
    """One concrete subclass per backend: nagini, velvet, lean, ears
    (`registry.BACKENDS` is the authoritative list)."""

    name: str
    language: LanguageTables

    @abstractmethod
    def check(self, path: Path, timeout: int = 300) -> VerifyResult:
        """Invoke the backend's checker on a solution file. Deterministic,
        read-only; for lean this judges the committed proofs (the gate layer
        additionally requires clean `#print axioms`)."""

    def check_source(self, src: str, timeout: int = 300) -> VerifyResult:
        from ..verify import verify_source_via
        return verify_source_via(self.check, src, self.language.solution_filename, timeout)

    @abstractmethod
    def conf_shadow(self, bundle_dir: Path) -> ShadowSpec | None:
        """Locate the executable shadow for G-CONF. None => the gate records
        an explicit skip (never a silent pass)."""

    @abstractmethod
    def verifier_tool_name(self) -> str:
        """Eval-agent tool name (nagini_verify / velvet_verify / lean_verify)."""

    def quickref(self) -> str:
        """Backend quick-reference block for eval prompts
        (prompts/<backend>/quickref.md)."""
        from ..prompts import load_prompt
        return load_prompt("quickref", backend=self.name)
