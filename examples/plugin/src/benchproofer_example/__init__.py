# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A third-party Benchproofer plugin, in as few lines as the interfaces allow.

Two components, registered through the same entry-point groups the built-in ones
use:

* `benchmark.MiniBenchmark` is a benchmark adapter over three tasks it ships itself,
  so it can be ingested with no network and no dataset.
* `gate.NoTodoGate` is a gate that refuses a specification with unfinished business
  left in it.
"""

from __future__ import annotations

from .benchmark import MiniBenchmark
from .gate import NoTodoGate

__all__ = ["MiniBenchmark", "NoTodoGate"]
