#!/usr/bin/env python3
"""G-CONF differential conformance for scikit-learn__scikit-learn-26323.

Refutes (does not prove) the R/I refinement leg of refinement.md: the modeled
selection `broadcastTargets` (which components the output-config broadcast
reaches) transliterated to Python, vs the PATCHED `set_output` selection block.

ORACLE CHOICE — why we transliterate the patched selection block instead of
driving `ColumnTransformer.set_output` end-to-end:
  `set_output` does not RETURN which components it configured; it calls
  `_safe_set_output(trans, transform=...)` for its side effect (flipping each
  child's output-config flag) and returns `self`. Recovering "which components
  were reached" end-to-end would require building a real `ColumnTransformer`
  with real estimators and reading back each child's private output-config
  state after the call — heavy, and it would not isolate the modeled behavior
  (the *selection*). Per the worker prompt, the ORACLE is therefore the
  **patched** selection block transliterated VERBATIM from the post-image of
  `set_output` (sklearn/compose/_column_transformer.py): the listed
  sub-transformers with the `{"passthrough","drop"}` sentinels filtered, then
  `self.remainder` appended when `self.remainder not in {"passthrough","drop"}`.
  We instrument that block with a recording stub in place of `_safe_set_output`
  so the ORACLE yields exactly the ordered list of reached components. The
  SHADOW is the modeled `broadcastTargets` from Solution.lean.

  We differential-test SHADOW vs ORACLE over fuzzed component lists. Exit 0 iff
  zero disagreements. stdlib only; the fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 26323
N_FUZZ = 100_000

SENTINELS = {"passthrough", "drop"}


def is_real(comp):
    """A component is a real estimator iff it is not a placeholder sentinel.
    mapping.md §2: `Component.real n` ↔ a real estimator; `Component.marker` ↔
    one of the sentinel strings."""
    return comp not in SENTINELS


# --- SHADOW: broadcastTargets / selectReal, transliterated -------------------
def shadow(listed, extra):
    """broadcastTargets (Solution.lean pure region), transliterated to Python.

    selectReal listed ++ (if isReal extra then [extra] else []).
    The backward `while` fold of collectBroadcastTargets computes exactly this
    left-to-right selection."""
    out = [c for c in listed if is_real(c)]
    if is_real(extra):
        out = out + [extra]
    return out


# --- ORACLE: the PATCHED set_output selection block, instrumented ------------
def oracle(listed, extra):
    """The post-image of `ColumnTransformer.set_output`, transliterated verbatim
    with `_safe_set_output` replaced by a recorder. `listed` already models the
    post-filter `transformers` generator value (sentinels in `self.transformers`
    are filtered by the generator's `if trans not in {...}`); we keep the filter
    explicit here so the ORACLE matches the real generator semantics.

    Post-image (sklearn/compose/_column_transformer.py:304-313):

        transformers = (trans for _, trans, _ in chain(...)
                        if trans not in {"passthrough", "drop"})
        for trans in transformers:
            _safe_set_output(trans, transform=transform)        # -> record
        if self.remainder not in {"passthrough", "drop"}:
            _safe_set_output(self.remainder, transform=transform)  # -> record
    """
    reached = []

    def _safe_set_output(trans):          # recorder stub for the side-effecting callee
        reached.append(trans)

    transformers = (t for t in listed if t not in SENTINELS)
    for trans in transformers:
        _safe_set_output(trans)
    if extra not in SENTINELS:
        _safe_set_output(extra)
    return reached


def fuzz_inputs(n, rng):
    # A component is either a sentinel or a real estimator (modeled by a unique id).
    def rand_component(uid):
        r = rng.random()
        if r < 0.25:
            return "passthrough"
        if r < 0.5:
            return "drop"
        return uid                         # a distinct real estimator (its identity)

    # boundary cases first (plan §4.1 step 4)
    yield ([], "drop")                     # default remainder, no transformers
    yield ([], "passthrough")
    yield ([], 0)                          # remainder estimator only (the reported bug)
    yield (["passthrough", "drop"], 0)     # all-sentinel listed + real remainder
    yield ([1, 2], "drop")                 # real listed, sentinel remainder
    yield ([1, 2], 0)                      # real listed + real remainder
    yield ([1, "drop", 2], "passthrough")
    yield (["drop"], "drop")
    yield ([1], 1)                         # same identity listed & remainder (still appended)

    uid = 1000
    for _ in range(n):
        k = rng.randint(0, 8)
        listed = []
        for _ in range(k):
            listed.append(rand_component(uid))
            uid += 1
        extra = rand_component(uid)
        uid += 1
        yield (listed, extra)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for listed, extra in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s = shadow(listed, extra)
        o = oracle(listed, extra)
        if s != o:
            disagreements.append((listed, extra, s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for listed, extra, s, o in disagreements:
            print("  listed=%r extra=%r shadow=%r oracle=%r" % (listed, extra, s, o))
        return 1
    print("G-CONF OK: R/I shadow of collectBroadcastTargets agrees with the "
          "patched set_output selection block on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
