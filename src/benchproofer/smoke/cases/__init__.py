# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The cases themselves, grouped by what they exercise.

Every module here exposes ``CASES``, a tuple of `benchproofer.smoke.model.Case`.
`benchproofer.smoke.suites` collects them; nothing else imports these modules, so a
new group is one file plus one line in that collector.

A case is written to the tool's public interface, the same one a user's script would
call, and it asserts something a user would care about. It does not reach into
private helpers, and it does not assert an implementation detail such as the order
in which gates happen to be listed. Those belong in the unit tests, which are much
cheaper to run and much easier to change.
"""

from __future__ import annotations

__all__: list[str] = []
