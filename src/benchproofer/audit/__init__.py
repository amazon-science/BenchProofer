# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Reviewing a bundle adversarially.

This package attacks artifacts; like the drafting package, it never decides whether
what it found counts. It writes attacks and judgments into the bundle's `audit`
directory, and the gates re-run the attacks and check the judgments for currency
afterwards. That order is the point: a review is evidence submitted for checking, not
a verdict, so a reviewer that overstates a finding produces nothing.

The public surface is `Reviewers`, which turns a `Bundle` into an `Audit` with one agent
session per auditor. `prompts` is the template library it sends, exposed because a project
with an unusual benchmark may want to reuse or override them.
"""

from __future__ import annotations

from . import prompts
from .agents import Reviewers
from .session import JUDGED_ROLES, ROLE_READS, Audit, Filed

__all__ = [
    "JUDGED_ROLES",
    "ROLE_READS",
    "Audit",
    "Filed",
    "Reviewers",
    "prompts",
]
