# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Pipeline configuration knobs.

The 300 s verification cap bounds one checker invocation (nagini/velvet) or
the TOTAL lean proof-phase budget.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

VERIFY_TIMEOUT_DEFAULT = 300
CONSTRUCT_TIMEOUT_DEFAULT = 3600


def _env_int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v and v.isdigit() else default


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip() not in ("", "0", "false", "False")


@dataclass
class ProofConfig:
    """Lean proof-phase config (construct P1.5). proof_gen is a TOTAL budget
    shared across attempts; "ok" only ever comes from a mechanical G-VERIFY
    re-check, never the agent's self-report."""
    proof_gen: int = VERIFY_TIMEOUT_DEFAULT
    max_proof_attempts: int = 1
    # True: a `stuck` drives the axiom-propose refinement loop.
    axiom_refinement: bool = False
    max_axiom_iterations: int = 10

    @classmethod
    def from_env(cls) -> "ProofConfig":
        return cls(
            proof_gen=_env_int("SBU_PROOF_GEN_TIMEOUT", VERIFY_TIMEOUT_DEFAULT),
            max_proof_attempts=_env_int("SBU_MAX_PROOF_ATTEMPTS", 1),
            axiom_refinement=_env_flag("SBU_AXIOM_REFINEMENT"),
            max_axiom_iterations=_env_int("SBU_MAX_AXIOM_ITERATIONS", 10),
        )
