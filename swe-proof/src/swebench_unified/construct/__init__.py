# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchmark-construction mode (docs/architecture.md §3): the build_one lifecycle
plus the run_all parallel runner."""
# `release_prose` holds the reference rules `publish_narration` and
# `verdict_surgery` read, and re-exports both at the foot of its own file, so it
# must run FIRST. Importing it here makes that true however a caller reaches the
# package: importing either sibling directly still gets a loaded `release_prose`
# rather than a half-initialised one.
from . import release_prose  # noqa: F401
