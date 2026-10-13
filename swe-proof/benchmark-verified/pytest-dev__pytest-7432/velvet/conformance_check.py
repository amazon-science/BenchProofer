#!/usr/bin/env python3
"""G-CONF differential conformance for pytest-dev__pytest-7432 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`reportSkipLocation`) is the report post-processing the
gold patch changes in `pytest_runtest_makereport`:

    elif (                                  # <-- gold change: elif -> standalone if
        item._store.get(skipped_by_mark_key, True)
        and rep.skipped
        and type(rep.longrepr) is tuple
    ):
        _, _, reason = rep.longrepr
        filename, line = item.reportinfo()[:2]
        assert line is not None
        rep.longrepr = str(filename), line + 1, reason

The CHANGED behaviour the spec pins is a SIDE EFFECT on a live pytest run: a
marker-induced skip's reported location must be rewritten to the test's own
definition (`SKIPPED [1] test_sample.py:2:`) EVEN WHEN `--runxfail` is given,
rather than left pointing inside the framework
(`SKIPPED [1] src/_pytest/skipping.py:NNN:`). Converting the trailing `elif` into
a standalone `if` decouples the correction from the earlier classification arms
(one of which, the `--runxfail` pass-through, otherwise consumes the report and
skips the correction).

There is no pytest-free, input-dependent R/I shadow to differential-test:

  * The discriminating observable (`locatedAtItem`) materializes only when the
    full pytest collection + runtest protocol executes a real test item under a
    real config: to observe "the reported location was corrected" one must run
    `pytest -rs [--runxfail]` over a test file through the real
    `pytest_runtest_makereport` hook wrapper and read the terminal summary — i.e.
    the F2P test itself (`test_xfail_run_with_skip_mark[test_input1-expected1]`,
    `result.stdout.fnmatch_lines(["SKIPPED [1] test_sample.py:2: ...", ...])`),
    not a pure transliteration this gate can fuzz over >=1e5 inputs.
  * The classified report (`rep`) and `priorClassification` are FREE INPUTS
    produced by the UNCHANGED classification chain (mapping.md section 3); their
    R/I shadow is a pass-through with no input-dependent computation to refute.
    The changed op's content is the structural decision `markSkipped and
    rep.skipped and rep.longreprIsTuple` made INDEPENDENTLY of
    `priorClassification`, whose only shadow is a constant decision over presence
    bits — diffing it carries no information the spec (G-VERIFY) does not already
    pin.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the modeled op's only observable
is a side effect on a live framework run with no offline R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub (precedent:
django__django-11451, django__django-11179). Soundness of the modeled behaviour
is carried instead by G-VERIFY (the spec provably forces `out = fixSkipLocation
markSkipped rep` — the correction depends only on the marker/skipped/tuple
observations, never on `xfailReportingOff` or `priorClassification`) and G-DIFF
(the prepatch, which gates the correction behind `!priorClassification`, fails
exactly the `locatedAtItem = true` clause when an earlier arm fired). See
mapping.md section 4 and refinement.md sections B/D.
"""
import sys


def main():
    print("G-CONF status=skip: pytest-dev__pytest-7432 — the modeled do-block is "
          "the skip-location correction of pytest_runtest_makereport, whose only "
          "discriminating observable is a side effect on a live pytest run (a "
          "marker-skip report's location rewritten to the test definition even "
          "under --runxfail, vs left pointing inside the framework); the "
          "classified report and the prior-classification flag are free inputs "
          "from the unchanged classification chain. No pytest-free, "
          "input-dependent R/I shadow exists. conf_skip=true. Soundness covered "
          "by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
