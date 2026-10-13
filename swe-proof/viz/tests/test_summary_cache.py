# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The board's summary tables must never make a visitor wait for an expiry.

`green_counts` reads one summary table per backend of both benchmarks and
`base.html` renders it in the header of every page, so recomputing them on the
request path puts a whole-corpus scan in front of one visitor per TTL. These
tests pin the property that fixes it: a cold key computes synchronously, an
expired key serves the stale value and refreshes behind the request, and a
refresh that raises keeps serving what it had.
"""
import threading
import time

import pytest

from backend import data


@pytest.fixture(autouse=True)
def _empty_cache():
    data._ttl_store.clear()
    data._ttl_refreshing.clear()
    yield
    data._ttl_store.clear()
    data._ttl_refreshing.clear()


def _settled(key, timeout=5.0):
    """Wait for the background refresh of `key` to finish."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if key not in data._ttl_refreshing:
            return True
        time.sleep(0.01)
    return False


def test_a_cold_key_is_computed_on_the_request():
    calls = []
    got = data._ttl_cached("cold", lambda: calls.append(1) or "value")
    assert got == "value"
    assert len(calls) == 1


def test_a_warm_key_does_not_recompute():
    data._ttl_cached("warm", lambda: "first")
    calls = []
    for _ in range(5):
        assert data._ttl_cached("warm", lambda: calls.append(1) or "second") == "first"
    assert calls == []


def test_an_expired_key_serves_stale_and_refreshes_behind_the_request():
    data._ttl_store["k"] = (time.monotonic() - data._TTL_S - 1, "stale")
    started = threading.Event()
    release = threading.Event()

    def slow():
        started.set()
        release.wait(5.0)
        return "fresh"

    # The point of the test: this call returns while `slow` is still running.
    assert data._ttl_cached("k", slow) == "stale"
    assert started.wait(5.0), "the refresh never started"
    release.set()
    assert _settled("k")
    assert data._ttl_cached("k", lambda: "unused") == "fresh"


def test_one_refresh_at_a_time_however_many_requests_arrive():
    data._ttl_store["k"] = (time.monotonic() - data._TTL_S - 1, "stale")
    release = threading.Event()
    calls = []

    def slow():
        calls.append(1)
        release.wait(5.0)
        return "fresh"

    for _ in range(10):
        assert data._ttl_cached("k", slow) == "stale"
    release.set()
    assert _settled("k")
    assert len(calls) == 1, f"{len(calls)} refreshes for 10 requests"


def test_a_failing_refresh_keeps_serving_the_stale_value():
    data._ttl_store["k"] = (time.monotonic() - data._TTL_S - 1, "stale")

    def boom():
        raise RuntimeError("the corpus moved under us")

    assert data._ttl_cached("k", boom) == "stale"
    assert _settled("k")
    # Re-stamped, so the retry is one TTL away rather than on the next request.
    assert data._ttl_cached("k", lambda: "unused") == "stale"


def test_the_real_summary_table_is_served_from_the_cache():
    """End to end over the shipped corpus: the second read does no work."""
    rows = data.summary_table("verified", "lean")
    assert rows, "no rows for verified/lean"
    t0 = time.monotonic()
    again = data.summary_table("verified", "lean")
    assert again is rows
    assert time.monotonic() - t0 < 0.5
