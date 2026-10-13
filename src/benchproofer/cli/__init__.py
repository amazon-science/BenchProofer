# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The command-line interface.

    from benchproofer.cli import app

The commands are thin: each resolves settings, calls one function in
`benchproofer.pipeline`, and renders the result. Anything worth scripting is in the
library, so a program that needs a different loop imports the pipeline directly
rather than driving this interface.
"""

from __future__ import annotations

from .main import app, main

__all__ = ["app", "main"]
