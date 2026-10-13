# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The pipeline: ingest, build, adjudicate, report.

Each stage is a plain function over explicit inputs, and each writes its result to
disk before the next one reads it. That is what makes a run resumable and what keeps
building separate from judging: the bundle, not a process, is the state of the work.

    from benchproofer.pipeline import adjudicate, build, execute, ingest

`execute` is the whole loop for a list of tasks. The stages underneath it are public
because a project that wants a different loop, a different order, or its own
concurrency should not have to reimplement them.
"""

from __future__ import annotations

from .adjudicate import (
    ORACLE_REQUIRED,
    STATIC_REQUIRED,
    Adjudication,
    adjudicate,
    bundles_under,
    certify,
    required_gates,
)
from .build import BuildResult, build, write_formalization
from .ingest import Ingestion, ingest, load_tasks, stream_tasks
from .report import BundleRow, Report, collect, summarize, write_report
from .run import Progress, RunResult, TaskOutcome, execute, judge_bundles

__all__ = [
    "ORACLE_REQUIRED",
    "STATIC_REQUIRED",
    "Adjudication",
    "BuildResult",
    "BundleRow",
    "Ingestion",
    "Progress",
    "Report",
    "RunResult",
    "TaskOutcome",
    "adjudicate",
    "build",
    "bundles_under",
    "certify",
    "collect",
    "execute",
    "ingest",
    "judge_bundles",
    "load_tasks",
    "required_gates",
    "stream_tasks",
    "summarize",
    "write_formalization",
    "write_report",
]
