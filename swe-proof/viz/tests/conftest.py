# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared bootstrap for the review-site tests.

`import backend.*` needs `viz/` on `sys.path`, so that happens once here: pytest
imports this file before any test module in this directory, however few of them
were selected.
"""
import sys
import tempfile
from pathlib import Path

import pytest

VIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIZ))

from backend import paths  # noqa: E402

# Never the operational database. `viz/data/review.sqlite` is real review
# history, several tests post comments, and `comments` caches its connection on
# first use -- so the redirect has to be in place before a module imports the app.
paths.REVIEW_DB = Path(tempfile.mkdtemp()) / "review_test.sqlite"

from backend import comments, settings  # noqa: E402

# Comments are OFF in a released deployment (`settings.COMMENTS_ENABLED`): the
# published site is static, and the comment form is the only part of it that
# writes. Most of the suite exercises the ENABLED behaviour, so the bootstrap
# turns the flag on and creates the scratch schema itself rather than relying on
# the app's startup hook, which is now guarded by the same flag.
# `test_comments_are_off_unless_a_deployment_opts_in` turns it back off for the
# one test that measures the default.
settings.COMMENTS_ENABLED = True
comments.init_db()


@pytest.fixture(autouse=True)
def _comments_on():
    """Re-assert the flag per test: `test_benchmark_rows` reloads `settings`, and
    a reload restores the env default (off), which would otherwise make the
    comment tests depend on module order."""
    settings.COMMENTS_ENABLED = True
    yield

# One SWE-bench Pro cell, for the routes, the boards and the comment threads. Every
# Pro instance here comes from a copyleft repository, so the release omits its dataset
# row, twins, maps and gate records (README, "Copyleft material"), and its page has
# to render from the pointer left in their place.
IID = ("instance_ansible__ansible-0ea40e09d1b35bcb69ff4d9cecf3d0defa4b36e8"
       "-v30a923fb5c164d6cd18280c02422f75e611e8fb2")
BM = "pro"

# One committed fully-green nagini bundle with prepatch twins in every backend, for
# the tests that read a cell's full artifact set or its dataset row. It has to be a
# Verified cell, since no Pro cell ships those.
FULL_BM = "verified"
FULL_IID = "astropy__astropy-12907"

# (benchmark key, bundle dir, the SBU_BENCHMARK name scripts/green_check.py wants)
CELLS = (("pro", "benchmark-pro", "swe_bench_pro_python"),
         ("verified", "benchmark-verified", "swe_bench_verified"))


def require_mirror(bm: str, instance_id: str) -> Path:
    """The bare mirror for a cell, or SKIP naming how to get one.

    Mirrors are a fetched input (`scripts/setup_repos.py`) and they are gigabytes,
    so a fresh checkout legitimately has none. A test that reads repository history
    is then UNANSWERABLE rather than failing: a red suite on a missing download
    says nothing about the code, and teaches a reader to ignore red.
    """
    mirror = paths.mirror_for(bm, instance_id)
    if mirror is None:
        pytest.skip(f"no bare mirror for {bm}/{instance_id}; "
                    f"run scripts/setup_repos.py")
    return mirror


def corpus_size(bm: str) -> int:
    """How many instances a benchmark row ships, counted off the filesystem.

    The boards must cover the whole row; a literal here would pin the corpus as
    it stood the day the test was written instead of that property.
    """
    root = paths.bench_root(bm)
    return sum(1 for d in root.iterdir()
               if d.is_dir() and ((d / "instance.json").is_file()
                                  or (d / "upstream.json").is_file()))
