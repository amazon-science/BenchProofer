# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The smoke suite: does this installation actually work, here, on real benchmarks.

The suite is not a substitute for the unit tests. It answers a different question:
whether the components that depend on the machine (dataset adapters, verifier
toolchains, container runtimes, model providers) do what the tool claims once they
are installed. Every case is declarative, so the suite reports what it could not
check as clearly as what it did.

Run it from the command line::

    benchproofer smoke offline      # nothing but the packaged fixtures
    benchproofer smoke all          # everything this machine can reach

or from Python::

    from benchproofer.smoke import run_suite
    result = run_suite("offline", settings=settings, workspace=Path("build/smoke"))
"""

from __future__ import annotations

from .model import Case, CaseResult, CaseStatus, Context, Failure, Observation, Unmet
from .report import SuiteResult, write_smoke_report
from .runner import run_cases, run_suite
from .suites import GROUPS, SUITES, cases, select

__all__ = [
    "GROUPS",
    "SUITES",
    "Case",
    "CaseResult",
    "CaseStatus",
    "Context",
    "Failure",
    "Observation",
    "SuiteResult",
    "Unmet",
    "cases",
    "run_cases",
    "run_suite",
    "select",
    "write_smoke_report",
]
