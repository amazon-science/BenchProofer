#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7490 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model has no PSeq inputs and no @Pure
helper functions; the only model-level callee is the @Pure @ContractOnly
`evaluate_marks` axiom, which per the contract is bridged to the REAL repo
callee `_pytest.skipping.evaluate_xfail_marks` (the axiom's repo counterpart
per mapping.md section 3.1). `SavedSlot` copies over as a plain
attribute-holder class.

ORACLE: the REAL repo operation the model models per mapping.md section 1 —
the post-yield portion of the `pytest_runtest_call` hookwrapper in
`_pytest.skipping` (the settle/refresh of the saved xfail evaluation against
the marks as they finally stand). The gate applies the diff to /testbed
before this script runs; PYTHONPATH=/testbed makes `_pytest` importable.
This script never applies any diff itself.

Driving the oracle: `pytest_runtest_call` is a hookwrapper generator, so each
trial advances it to its `yield` with a benign neutral state (no marks, an
empty saved evaluation — the pre-yield section then neither raises nor leaves
anything meaningful), installs the trial's pre-state and final marker state
while the body would be running, and resumes it to completion. The state at
the resume point is exactly the model's `Old(slot)` / `final_marker_state`.

Type bridge (mapping.md section 2):
  store key absent under the saved-evaluation key   -> present == False
  store key holds None                              -> present == True, value is None
  store key holds an Xfail                          -> present == True, value is not None
  the item's final set of marks                     -> opaque marker-state token
The opaque token is realised here as the collected item carrying the trial's
final marker configuration; `evaluate_marks(token)` invokes the REAL
`evaluate_xfail_marks` on it (deterministic in the marker state, per the
axiom G-AX validates). Values are compared by attrs equality plus
None-ness; a preserved prior evaluation is additionally checked by identity
(the same object goes into both the shadow's and the oracle's pre-state).

Input domain: all trials satisfy the model's Requires (a slot with both
fields is always supplied). Marker configurations stay within the callee's
non-raising domain (boolean/absent conditions only, no string conditions):
mapping.md's directive-7 note records that raising marker states are outside
the domain the proof consumes, so they are not conformance-relevant inputs.

>= 1e5 Requires-satisfying inputs: structured boundary cases (every
pre-state kind x every marker-menu entry) plus 100000 fuzz trials.
Pinned fuzz seed: 749034.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (plain random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 749034
N_FUZZ = 100_000

MISSING = object()  # sentinel: the saved-evaluation key is absent


# --- SavedSlot from model.py, contracts stripped -------------------------------

class SavedSlot:
    def __init__(self, present, value):
        self.present = present
        self.value = value


# --- bridge for the axiomatized callee ------------------------------------------
# The model's @Pure @ContractOnly `evaluate_marks(marker_state)` is the REAL
# repo callee applied to the marker state the token stands for. Here a token
# IS the item carrying that marker configuration; the real callee is bound in
# main() after the repo import.

_REAL_EVALUATE = None


def evaluate_marks(marker_state):
    return _REAL_EVALUATE(marker_state)


# --- the impl region of model.py, verbatim, contract calls stripped -------------

def settle_saved_evaluation(slot, final_marker_state):
    if not slot.present:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True
    elif slot.value is None:
        slot.value = evaluate_marks(final_marker_state)
        slot.present = True


# --- oracle driver ---------------------------------------------------------------

def run_real_settle(sk, item, xfailed_key, pre_state, final_marks):
    """Drive the REAL hookwrapper through one trial. Returns the post-run
    (present, value) of the saved slot, read back off the item's store."""
    # Benign neutral state for the pre-yield section: no marks, an empty
    # (None) saved evaluation -> the pre-yield section re-evaluates to None
    # and does not raise.
    item.own_markers = []
    item._store[xfailed_key] = None
    gen = sk.pytest_runtest_call(item)
    next(gen)  # advance to the yield
    # Install the trial pre-state of the saved slot...
    if pre_state is MISSING:
        del item._store[xfailed_key]
    else:
        item._store[xfailed_key] = pre_state
    # ...and the marks as they finally stand (what a test body may have
    # attached while running).
    item.own_markers = list(final_marks)
    try:
        next(gen)  # resume past the yield to completion
    except StopIteration:
        pass
    value = item._store.get(xfailed_key, MISSING)
    if value is MISSING:
        return (False, None)
    return (True, value)


def check_one(sk, item, xfailed_key, pre_state, final_marks, label):
    real_present, real_value = run_real_settle(sk, item, xfailed_key,
                                               pre_state, final_marks)
    # Shadow input under the bridge: absent key -> present False; the item
    # (already carrying final_marks) is the final marker-state token.
    if pre_state is MISSING:
        slot = SavedSlot(False, None)
    else:
        slot = SavedSlot(True, pre_state)
    settle_saved_evaluation(slot, item)

    ok = (slot.present == real_present
          and (slot.value is None) == (real_value is None)
          and slot.value == real_value)
    if ok and pre_state is not MISSING and pre_state is not None:
        # A meaningful prior evaluation must be the one that stands, by
        # identity, on both sides (the same object was installed in both).
        ok = slot.value is pre_state and real_value is pre_state
    if not ok:
        return ("DISAGREEMENT [%s]\n  pre_state=%r\n  final_marks=%r\n"
                "  shadow=(present=%r, value=%r)\n"
                "  real=(present=%r, value=%r)"
                % (label, pre_state, final_marks,
                   slot.present, slot.value, real_present, real_value))
    return None


# --- input generation --------------------------------------------------------------

def mark_menu(pytest):
    """Final-marker-state configurations, all within the callee's non-raising
    domain (boolean/absent conditions only)."""
    xf = pytest.mark.xfail
    return [
        [],                                                    # no marks at all
        [xf(reason="dyn").mark],                               # plain dynamic xfail
        [xf(True, reason="cond-true").mark],                   # applicable condition
        [xf(False, reason="cond-false").mark],                 # inapplicable condition
        [xf(reason="norun", run=False).mark],
        [xf(reason="strict", strict=True).mark],
        [xf(reason="raises", raises=ValueError).mark],
        [xf(False, reason="a").mark, xf(reason="b").mark],     # first applicable wins
        [xf(reason="a").mark, xf(reason="b", strict=True).mark],
        [pytest.mark.skip(reason="not-an-xfail").mark],        # non-xfail noise
        [pytest.mark.skip(reason="s").mark, xf(reason="mixed").mark],
    ]


def pre_state_menu(Xfail):
    """Saved-slot pre-states covering the three carrier cases of mapping.md
    section 2 (absent / present-empty / present-non-empty, with assorted
    field values in the non-empty case)."""
    return [
        MISSING,                                # nothing saved
        None,                                   # saved but empty evaluation
        Xfail("prior", True, False, None),
        Xfail("prior-norun", False, False, None),
        Xfail("prior-strict", True, True, None),
        Xfail("", True, False, None),
    ]


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    import pytest
    import _pytest.skipping as sk
    from _pytest.skipping import Xfail, evaluate_xfail_marks, xfailed_key

    global _REAL_EVALUATE
    _REAL_EVALUATE = evaluate_xfail_marks

    # Obtain one real collected Item to serve as the marker-state carrier.
    import os
    import tempfile
    items_box = {}

    class _Collect:
        def pytest_collection_modifyitems(self, items):
            items_box["items"] = list(items)

    workdir = tempfile.mkdtemp(prefix="gconf7490_")
    modpath = os.path.join(workdir, "test_conf_sample.py")
    with open(modpath, "w") as fh:
        fh.write("def test_plain():\n    pass\n")
    pytest.main(["--collect-only", "-p", "no:cacheprovider", modpath],
                plugins=[_Collect()])
    items = items_box.get("items", [])
    if not items:
        print("ERROR: collection produced no items")
        return 1
    item = items[0]

    checked = 0

    # Boundary: full cross product of pre-state kinds x marker configurations.
    n_boundary = 0
    for pre in pre_state_menu(Xfail):
        for marks in mark_menu(pytest):
            err = check_one(sk, item, xfailed_key, pre, marks, "boundary")
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    # Fuzz: random pre-state x random marker configuration, with randomised
    # Xfail field values so tokens/prior values vary. Pinned seed above.
    rng = random.Random(SEED)
    menu = mark_menu(pytest)
    xf = pytest.mark.xfail
    for i in range(N_FUZZ):
        kind = rng.random()
        if kind < 0.3:
            pre = MISSING
        elif kind < 0.6:
            pre = None
        else:
            pre = Xfail("r%d" % rng.randint(0, 999), rng.random() < 0.5,
                        rng.random() < 0.5,
                        None if rng.random() < 0.7 else (ValueError,))
        if rng.random() < 0.6:
            marks = menu[rng.randrange(len(menu))]
        else:
            marks = []
            for _ in range(rng.randint(0, 3)):
                kwargs = {"reason": "f%d" % rng.randint(0, 999)}
                if rng.random() < 0.3:
                    kwargs["run"] = rng.random() < 0.5
                if rng.random() < 0.3:
                    kwargs["strict"] = rng.random() < 0.5
                if rng.random() < 0.5:
                    marks.append(xf(rng.random() < 0.5, **kwargs).mark)
                else:
                    marks.append(xf(**kwargs).mark)
        err = check_one(sk, item, xfailed_key, pre, marks, "fuzz#%d" % i)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real post-yield settle of the saved "
          "xfail evaluation on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "axiom callee bound to the real evaluator)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
