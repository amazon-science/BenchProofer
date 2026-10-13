# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`python -m swebench_unified.eval` — the mechanical consumer scorer
(score mode: verified => resolved over a predictions dir; see eval/score.py).
The frontier-model evaluation harness is `python -m swebench_unified.eval.run`."""
import sys

from .score import main

sys.exit(main())
