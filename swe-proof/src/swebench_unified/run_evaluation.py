# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Drop-in wrapper around `swebench.harness.run_evaluation` that applies our
documented harness patches (see harness_patches.py) before any test spec is
built. Use this instead of `python -m swebench.harness.run_evaluation`:

    python -m swebench_unified.run_evaluation <same CLI args>
"""
import runpy
import sys

import swebench_unified.harness_patches  # noqa: F401  (applies on import)

if __name__ == "__main__":
    sys.argv[0] = "swebench.harness.run_evaluation"
    runpy.run_module("swebench.harness.run_evaluation", run_name="__main__")
