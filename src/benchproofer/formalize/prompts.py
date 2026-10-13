# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The drafting stage's prompt templates, packaged under ``formalize/templates``.

A template includes a rules file as ``$<name>_rules`` (`Library.render`), so a rule drafting
shares with the auditors is written once, in ``core/templates``.
"""

from __future__ import annotations

from ..core.prompts import Library

__all__ = ["LIBRARY", "names", "render", "template"]

LIBRARY = Library("benchproofer.formalize")

template = LIBRARY.template
names = LIBRARY.names
render = LIBRARY.render
