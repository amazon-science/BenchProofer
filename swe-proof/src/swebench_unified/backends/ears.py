# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""EARS backend: natural-language EARS-format requirements (requirements.md),
NO formal verifier (docs/adding_a_backend.md §5).

`check()` runs the EARS structural LINT — a well-formedness judgment, not a
verification. Every surface that renders its result labels it as lint. The
verifier-backed gates (G-VERIFY/G-DIFF/G-GOLD/G-MUT/G-PBT/G-CONF/G-AX) do not
list "ears" in applies_to, so run_gates records explicit skips and nothing in
the gate layer ever calls check(); the eval harness reuses it as the agent's
lint tool and the verify-slot substitute (clearly labelled `lint`)."""
from __future__ import annotations

import time
from pathlib import Path

from ..verify import VerifyResult
from .base import Backend, LanguageTables, ShadowSpec


class EarsBackend(Backend):
    name = "ears"
    language = LanguageTables(
        flavor="ears",
        solution_filename="requirements.md",
        comment_line="",           # no code comments — the whole file is prose
        region_names=(),           # no marker regions; spec_view is identity
        import_allowlist=(),
        banned_tokens=(),
    )

    def check(self, path: Path, timeout: int = 300) -> VerifyResult:
        """EARS structural lint (there is no formal verifier). success = the
        document is well-formed EARS; stdout carries the lint report."""
        from ..ears_lint import lint
        start = time.monotonic()
        try:
            text = Path(path).read_text()
        except OSError as e:
            return VerifyResult(False, time.monotonic() - start, "",
                                f"cannot read {path}: {e}", returncode=2)
        ok, report = lint(text)
        return VerifyResult(ok, time.monotonic() - start,
                            f"EARS lint (no formal verifier): {report}", "",
                            returncode=0 if ok else 1)

    def conf_shadow(self, bundle_dir: Path) -> ShadowSpec | None:
        """No formal impl to shadow — G-CONF records an explicit skip."""
        return None

    def verifier_tool_name(self) -> str:
        """The eval agent's tool: the EARS lint (labelled as such — there is
        no verifier for this backend)."""
        return "ears_lint"
