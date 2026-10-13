#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7490 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl region (`refresh` /
             `finalXfail` over the `Option Xfail` carrier) transliterated to
             Python. There are NO A-tagged callees inside the impl region (the
             marker-evaluation callee's results are *inputs* — `evalBefore` /
             `evalAfter`), so the shadow is pure R/I (conf_skip = false).
  * ORACLE — `patch.diff`'s behaviour: the REAL patched
             `_pytest.skipping.pytest_runtest_call` generator, driven with a fake
             item over the mapping.md §2 bijection and a controllable
             `evaluate_xfail_marks` stub returning `evalBefore` on the first call
             and `evalAfter` on the second (i.e. the body may have changed the
             markers between pre- and post-yield — the dynamic-add case). The
             observable is the value stored under `xfailed_key` once the hook
             generator has completed, which is exactly what reporting consults.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the patched SWE-Bench instance image; G-RESOLVE applies the
gold patch first). stdlib + installed pytest only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

import _pytest.skipping as sk
from _pytest.skipping import Xfail, xfailed_key
from _pytest.store import Store


SEED = 7490
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean refresh / finalXfail -----------------------
def refresh(current, fresh):
    """`refresh` (pure region) transliterated."""
    return current if current is not None else fresh


def final_xfail(entry, eval_before, eval_after):
    """`finalXfail` (pure region) transliterated."""
    return refresh(refresh(entry, eval_before), eval_after)


def shadow(entry, eval_before, eval_after):
    return obs(final_xfail(entry, eval_before, eval_after))


# --- the oracle: the REAL patched pytest_runtest_call generator ---------------
class FakeOption:
    runxfail = False


class FakeConfig:
    option = FakeOption()


class FakeItem:
    def __init__(self):
        self._store = Store()
        self.config = FakeConfig()


def obs(xf):
    """Observable projection of an Optional[Xfail] (mapping.md §2)."""
    if xf is None:
        return None
    return (xf.reason, xf.run, xf.strict)


def oracle(entry, eval_before, eval_after):
    item = FakeItem()
    if entry is not None:
        item._store[xfailed_key] = entry

    # Controllable parametric callee: first evaluation (pre-yield) yields
    # eval_before; second evaluation (post-yield) yields eval_after. Modeling
    # the markers possibly changing while the body ran. Restored afterward.
    seq = [eval_before, eval_after]
    calls = {"n": 0}

    def fake_eval(_item):
        i = min(calls["n"], len(seq) - 1)
        calls["n"] += 1
        return seq[i]

    real_eval = sk.evaluate_xfail_marks
    sk.evaluate_xfail_marks = fake_eval
    try:
        gen = sk.pytest_runtest_call(item)
        next(gen)          # run pre-yield section
        try:
            next(gen)      # run post-yield section -> StopIteration
        except StopIteration:
            pass
    finally:
        sk.evaluate_xfail_marks = real_eval

    return obs(item._store.get(xfailed_key, None))


# All modeled determinations use run=True (mapping.md §2 flag dependency: the
# tested configuration; run=False routes through the unchanged pre-yield xfail()
# branch, orthogonal to which determination is stored).
def mk(tag):
    if tag is None:
        return None
    reason, strict = tag
    return Xfail(reason=reason, run=True, strict=strict, raises=None)


def fuzz_inputs(n, rng):
    # The distinct determinations we draw from (plus None).
    pool_tags = [
        None,
        ("xfail", False),
        ("xfail", True),
        ("", False),
        ("reason A", True),
        ("[NOTRUN] x", False),
    ]
    # boundary: full cross product of (entry, before, after)
    for e in pool_tags:
        for b in pool_tags:
            for a in pool_tags:
                yield (e, b, a)
    # randomized re-sampling to exceed the fuzz floor deterministically
    extra = ["üñîçødé", "a<b>&'\"", "x" * 40]
    tags = pool_tags + [(s, rng.random() < 0.5) for s in extra]
    for _ in range(n):
        yield (rng.choice(tags), rng.choice(tags), rng.choice(tags))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for e_tag, b_tag, a_tag in fuzz_inputs(N_FUZZ, rng):
        count += 1
        entry, before, after = mk(e_tag), mk(b_tag), mk(a_tag)
        sh = shadow(entry, before, after)
        orc = oracle(entry, before, after)
        if sh != orc:
            disagreements.append((e_tag, b_tag, a_tag, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, b, a, sh, orc in disagreements:
            print("  entry=%r before=%r after=%r shadow=%r oracle=%r"
                  % (e, b, a, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveDynamicXfail agrees with patch.diff "
          "behaviour (real patched pytest_runtest_call) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
