# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Read-only review/visualization backend for the verified twins.

Strictly read-only with respect to the dataset (the per-benchmark bundle roots
and the bare repo mirrors beside them). The ONLY writable surface is the comments
SQLite database under `viz/data/`.
"""
