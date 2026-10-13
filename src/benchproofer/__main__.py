# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run the CLI with ``python -m benchproofer``.

For a checkout, or an environment whose scripts directory is not on PATH.
"""

from __future__ import annotations

from .cli.main import main

if __name__ == "__main__":
    main()
