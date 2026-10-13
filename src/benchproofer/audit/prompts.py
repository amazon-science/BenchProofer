# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The review stage's prompt templates, packaged under ``audit/templates``.

A question is asked by an auditor, and what it is is stated by the ``<question>-rules``
template, which the session asking it includes as ``$<question>_rules`` (`Library.render`).
"""

from __future__ import annotations

from ..core.prompts import Library

__all__ = ["LIBRARY", "names", "render", "template"]

LIBRARY = Library("benchproofer.audit")

template = LIBRARY.template
names = LIBRARY.names
render = LIBRARY.render
