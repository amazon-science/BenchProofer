#!/usr/bin/env python3
"""G-AX soundness check for pytest-dev__pytest-7490 (plan §4).

`resolveDynamicXfail` models `pytest_runtest_call` parametrically over the result
of the UNCHANGED callee `evaluate_xfail_marks(item)`, taken as the abstract
inputs `evalBefore` / `evalAfter` (mapping.md §3.1). There is no consumed axiom;
the spec is quantified over every possible `Option Xfail` result. This script
validates the two properties the parametric model relies on, against the REAL
`_pytest.skipping.evaluate_xfail_marks`:

  P1 (pure in the marker set) — evaluating twice on the same item's markers
     yields the same determination.
  P2 (reflects markers present at call time) — an item with no xfail marker
     evaluates to None; once an xfail marker is present, it evaluates to an
     Xfail carrying that marker's reason/run/strict. This is what lets
     `evalAfter` be `some _` where `evalBefore` was `none` (the dynamic-add case).

Runs in-container against the installed pytest. Imports only stdlib + pytest.
Exit 0 iff sound.
"""
import random
import sys

from _pytest.skipping import evaluate_xfail_marks, Xfail


SEED = 7490
N_FUZZ = 20_000


class FakeConfig:
    """Minimal config: supplies the xfail_strict ini default."""
    def __init__(self, xfail_strict=False):
        self._xfail_strict = xfail_strict

    def getini(self, name):
        if name == "xfail_strict":
            return self._xfail_strict
        raise KeyError(name)


class FakeItem:
    """Minimal item exposing only what evaluate_xfail_marks reads:
    iter_markers(name=...) and config.getini(...)."""
    def __init__(self, marks, xfail_strict=False):
        # marks: list of _pytest.mark.structures.Mark
        self._marks = list(marks)
        self.config = FakeConfig(xfail_strict)

    def iter_markers(self, name=None):
        for m in self._marks:
            if name is None or m.name == name:
                yield m

    def add_marker(self, marker):
        # Mirrors Node.add_marker: append the underlying Mark.
        self._marks.append(marker.mark)


def make_xfail_mark(reason=None, run=None, strict=None, raises=None):
    import pytest
    kwargs = {}
    if reason is not None:
        kwargs["reason"] = reason
    if run is not None:
        kwargs["run"] = run
    if strict is not None:
        kwargs["strict"] = strict
    if raises is not None:
        kwargs["raises"] = raises
    return pytest.mark.xfail(**kwargs)


def obs(xf):
    """Observable projection of an Optional[Xfail] (mapping.md §2)."""
    if xf is None:
        return None
    return (xf.reason, xf.run, xf.strict)


def check_case(reason, run, strict, xfail_strict):
    failures = []

    # --- P2 part A: no xfail marker -> None
    empty = FakeItem([], xfail_strict=xfail_strict)
    before = evaluate_xfail_marks(empty)
    if before is not None:
        failures.append(("P2a: empty item not None", obs(before)))

    # --- P2 part B: add an xfail marker dynamically -> Xfail with that content
    mark = make_xfail_mark(reason=reason, run=run, strict=strict)
    empty.add_marker(mark)
    after = evaluate_xfail_marks(empty)
    if after is None:
        failures.append(("P2b: after add still None", None))
    else:
        # run defaults to True, strict defaults to the ini when omitted.
        exp_run = True if run is None else run
        exp_strict = xfail_strict if strict is None else strict
        exp_reason = "" if reason is None else reason
        if not isinstance(after, Xfail):
            failures.append(("P2b: not an Xfail", type(after).__name__))
        elif obs(after) != (exp_reason, exp_run, exp_strict):
            failures.append(("P2b: content mismatch",
                             (obs(after), (exp_reason, exp_run, exp_strict))))

    # --- P1: determinism — re-evaluate the same markers, same result
    again = evaluate_xfail_marks(empty)
    if obs(again) != obs(after):
        failures.append(("P1: non-deterministic", (obs(again), obs(after))))

    return failures


def main():
    rng = random.Random(SEED)
    all_failures = []
    count = 0

    # Boundary cases: default reason, empty reason, flag combinations.
    boundary = []
    for reason in (None, "", "xfail", "[NOTRUN] x", "üñîçødé reason"):
        for run in (None, True, False):
            for strict in (None, True, False):
                for xfail_strict in (False, True):
                    boundary.append((reason, run, strict, xfail_strict))
    for c in boundary:
        count += 1
        all_failures.extend(check_case(*c))

    # Randomized fuzz over reason strings + flag combinations.
    alphabet = "abc <>&\"'[]() üñ"
    for _ in range(N_FUZZ):
        count += 1
        rlen = rng.randint(0, 12)
        reason = "".join(rng.choice(alphabet) for _ in range(rlen))
        run = rng.choice([None, True, False])
        strict = rng.choice([None, True, False])
        xfail_strict = rng.choice([False, True])
        fs = check_case(reason, run, strict, xfail_strict)
        if fs:
            all_failures.extend(fs)
            if len(all_failures) >= 5:
                break

    if all_failures:
        print("G-AX FAIL: %d violation(s) of the parametric model over %d cases:"
              % (len(all_failures), count))
        for tag, detail in all_failures[:5]:
            print("  %s: %r" % (tag, detail))
        return 1
    print("G-AX OK: parametric model of evaluate_xfail_marks sound — "
          "pure in the marker set (P1) and reflects markers present at call "
          "time (P2: None with no marker, Xfail carrying reason/run/strict once "
          "added) on %d boundary + fuzz cases (seed=%d)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
