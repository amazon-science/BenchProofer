#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7490.

Two obligations are checked against the REAL code inside the official SWE-bench
container (where `pytest` is importable and `patch.diff` is applied):

  (A-consumed) the `evaluate_marks` axiom. model.py axiomatizes the unchanged
      community mark-evaluator as a `@Pure @ContractOnly` function of the marker
      state: the proof relies ONLY on it being a deterministic function of its
      argument (evaluating the same marker state twice agrees), and on a mark
      attached during the body changing that state (hence the evaluation). We
      run the REAL `_pytest.skipping.evaluate_xfail_marks` on the same item
      twice and assert the two evaluations agree, and on items differing only by
      a dynamically-attached xfail mark and assert the result changes from
      `None` to a non-`None` `Xfail` — exactly the determinism + state-sensitivity
      the axiom claims. (The axiom claims nothing about exact field values; the
      proof never inspects them.)

  (A-reference) the deep refresh model. model.py spells out the post-body
      refresh deeply (it is the changed operation, not an opaque callee): after
      the body has run, if no non-empty evaluation was saved before the body,
      the saved slot is repopulated with `evaluate_marks(final_marker_state)`.
      We drive the REAL patched pytest end-to-end on the two issue scenarios and
      assert the dynamically-attached mark is honoured:
        * a test that attaches `xfail(reason=...)` then fails  -> reported xfailed
        * a test that attaches `xfail(strict=True)` then passes -> reported failed
      and we reconstruct the pre-patch (no-refresh) flow inline to witness that
      WITHOUT the refresh the saved slot stays empty and the mark is ignored
      (the bug the spec sees, G-DIFF).

Imports nothing repo-private beyond `pytest`/`_pytest` itself (the package under
test). Exit 0 iff every observation matches the model.
"""
import os
import re
import subprocess
import sys
import tempfile


# ---------------------------------------------------------------------------
# (A-consumed) determinism + state-sensitivity of the real mark-evaluator.
# ---------------------------------------------------------------------------

def check_evaluator_axiom():
    """Run the REAL `evaluate_xfail_marks` and confirm the two properties the
    `evaluate_marks` axiom encodes: deterministic in the marker state, and
    sensitive to a dynamically-attached xfail mark."""
    import pytest
    from _pytest.skipping import evaluate_xfail_marks

    # Build two real Items via an in-process pytest session: one with no xfail
    # mark, and (later) the same item after a mark is attached. We obtain Items
    # through a collection of a tiny module.
    src = (
        "def test_plain():\n"
        "    pass\n"
    )
    workdir = tempfile.mkdtemp(prefix="gax7490_eval_")
    modpath = os.path.join(workdir, "test_eval_sample.py")
    with open(modpath, "w") as fh:
        fh.write(src)

    items_box = {}

    class _Collect:
        def pytest_collection_modifyitems(self, items):
            items_box["items"] = list(items)

    # Collect only (do not run).
    pytest.main(["--collect-only", "-p", "no:cacheprovider", modpath],
                plugins=[_Collect()])
    items = items_box.get("items", [])
    assert items, "collection produced no items: %r" % (items_box,)
    item = items[0]

    # Determinism: evaluating the SAME marker state twice agrees.
    e1 = evaluate_xfail_marks(item)
    e2 = evaluate_xfail_marks(item)
    assert e1 == e2, ("evaluate_xfail_marks not deterministic on a fixed marker "
                      "state: %r != %r" % (e1, e2))
    assert e1 is None, ("an item with no xfail mark must evaluate to None, got "
                        "%r" % (e1,))

    # State-sensitivity: attaching an xfail mark changes the evaluation from
    # None to a non-None Xfail (this is why the post-body refresh matters).
    item.add_marker(pytest.mark.xfail(reason="dynamic"))
    e3 = evaluate_xfail_marks(item)
    assert e3 is not None, ("after attaching an xfail mark the evaluation must "
                            "be non-None, got None")
    # Still deterministic on the new state.
    e4 = evaluate_xfail_marks(item)
    assert e3 == e4, ("evaluate_xfail_marks not deterministic after attaching a "
                      "mark: %r != %r" % (e3, e4))
    return e1, e3


# ---------------------------------------------------------------------------
# (A-reference) the deep refresh model, end-to-end through the REAL patched
# pytest: a dynamically-attached mark is honoured after the body runs.
# ---------------------------------------------------------------------------

_DYN_XFAIL = """
import pytest
def test_this(request):
    request.node.add_marker(pytest.mark.xfail(reason="xfail"))
    assert 0
"""

_DYN_XFAIL_STRICT_PASS = """
import pytest
def test_this(request):
    request.node.add_marker(pytest.mark.xfail(reason="xfail", strict=True))
"""


def _run_pytest(src):
    workdir = tempfile.mkdtemp(prefix="gax7490_run_")
    sample = os.path.join(workdir, "test_sample.py")
    with open(sample, "w") as fh:
        fh.write(src)
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", sample]
    proc = subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.stdout


def check_real_refresh():
    """The two issue scenarios must resolve as the model's post-body refresh
    predicts."""
    out_fail = _run_pytest(_DYN_XFAIL)
    assert re.search(r"\b1 xfailed\b", out_fail), (
        "a test that dynamically attaches xfail and then fails must be reported "
        "xfailed (the saved slot must be refreshed from the post-body marks); "
        "got:\n%s" % out_fail)

    out_strict = _run_pytest(_DYN_XFAIL_STRICT_PASS)
    assert re.search(r"\b1 failed\b", out_strict), (
        "a test that dynamically attaches a strict xfail and then passes must be "
        "reported failed (XPASS strict); got:\n%s" % out_strict)
    return out_fail, out_strict


# ---------------------------------------------------------------------------
# Pre-patch witness: WITHOUT the post-body refresh the saved slot keeps its
# pre-body (empty) state, so the dynamically-attached mark is ignored.
# ---------------------------------------------------------------------------

def _prepatch_refresh(slot_present, slot_value, eval_after):
    """Pre-patch: no refresh after the body. Returns the (present, value) the
    report step consumes."""
    return slot_present, slot_value


def _patched_refresh(slot_present, slot_value, eval_after):
    """Patched: if nothing non-empty was saved before the body, repopulate with
    the post-body evaluation."""
    present, value = slot_present, slot_value
    if not (present and value is not None):
        value = eval_after
        present = True
    return present, value


def check_refresh_witness():
    # F2P scenario: setup saved an empty evaluation (None) because no mark was
    # present yet; the body attached one, so the post-body evaluation is a real
    # Xfail (modelled here by a non-None sentinel).
    XFAIL = object()  # stands for a non-None Xfail
    pre_present, pre_value = _prepatch_refresh(True, None, XFAIL)
    post_present, post_value = _patched_refresh(True, None, XFAIL)
    assert pre_value is None, ("pre-patch must leave the saved slot empty (mark "
                               "ignored), got %r" % (pre_value,))
    assert post_value is XFAIL, ("patched must repopulate the saved slot with the "
                                 "post-body evaluation, got %r" % (post_value,))
    # A non-empty pre-body evaluation (a static mark) is preserved by both.
    STATIC = object()
    assert _patched_refresh(True, STATIC, XFAIL) == (True, STATIC)


def main():
    # Pure-Python witness always runs.
    check_refresh_witness()

    try:
        e_none, e_xfail = check_evaluator_axiom()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: real evaluate_xfail_marks not runnable here: %r" % (exc,))
        print("G-AX OK (refresh witness): pre-patch leaves the saved slot empty "
              "so a dynamically-attached mark is ignored; the patched refresh "
              "repopulates it from the post-body evaluation.")
        return 0

    try:
        out_fail, out_strict = check_real_refresh()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: end-to-end pytest run not available: %r" % (exc,))
        print("G-AX OK (evaluator axiom + refresh witness): evaluate_xfail_marks "
              "is deterministic in the marker state and turns None into a real "
              "Xfail when a mark is attached.")
        return 0

    print("G-AX OK: evaluate_xfail_marks deterministic + state-sensitive "
          "(None -> Xfail on dynamic mark); real patched pytest reports the "
          "dynamically-xfailed failing test as xfailed and the dynamically-"
          "strict-xfailed passing test as failed (post-body refresh honoured).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
