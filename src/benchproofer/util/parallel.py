# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Running one worker over many items.

Every stage is parallel over its unit of work (a task, a bundle, a smoke case) and wants
the results in the order the items were given; this is that loop, in one place. Workers
are threads, since the work waits on a subprocess or an HTTP request. Nothing here
catches exceptions, so a stage that must not be stopped by one item handles that in its
own worker.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

__all__ = ["mapped"]

_Item = TypeVar("_Item")
_Result = TypeVar("_Result")


def mapped(
    items: Sequence[_Item],
    worker: Callable[[_Item], _Result],
    *,
    workers: int = 1,
    prefix: str = "benchproofer",
) -> list[_Result]:
    """Apply ``worker`` to every item, returning the results in the items' order.

    Args:
        items: The work.
        worker: Called once per item.
        workers: How many at a time. One, or a single item, runs in this thread, so a
            sequential run has no pool in its traceback.
        prefix: Thread name prefix, for a readable stack dump.
    """
    count = max(1, workers)
    if count == 1 or len(items) <= 1:
        return [worker(item) for item in items]
    with ThreadPoolExecutor(max_workers=count, thread_name_prefix=prefix) as pool:
        return list(pool.map(worker, items))
