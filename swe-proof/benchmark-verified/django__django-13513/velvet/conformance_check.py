#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13513 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — `flattenSeq` from Solution.lean's impl region (the modeled changed
              assembly op), transliterated to Python over the *real* repo type
              via the mapping.md bijection (a per-exception frame list ↔ a
              `list` of tokens; the chain ↔ a `list` of such lists). `flattenSeq`
              is the in-order concatenation of every item's entries, skipping
              (not halting on) empty items.

  * ORACLE  — `patch.diff`'s behaviour: the gold-patched assembly portion of
              `ExceptionReporter.get_traceback_frames`, transliterated VERBATIM
              (mapping.md §3.1):

                  exc_value = exceptions.pop()
                  tb = self.tb if not exceptions else exc_value.__traceback__
                  frames.extend(self.get_exception_traceback_frames(exc_value, tb))
                  while exceptions:
                      exc_value = exceptions.pop()
                      frames.extend(self.get_exception_traceback_frames(
                          exc_value, exc_value.__traceback__))
                  return frames

              The unchanged per-exception frame walk
              `get_exception_traceback_frames` is the carrier itself (mapping.md
              §3.1): each chain element IS that walk's output, so the oracle's
              `extend` operates directly on the per-exception token lists.

They must agree on every input. The discriminating inputs are chains containing
an EMPTY item (an exception whose traceback is empty) in any position — the
pre-patch loop halted there and dropped every later exception's frames; the
patched assembly (and `flattenSeq`) does not. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample.

Runs stdlib-only; the fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. No callee is abstracted (no axioms), so nothing is left as a real
repo callee — G-AX is skipped for this bundle.
"""
import random
import sys

SEED = 13513
N_FUZZ = 100_000


# --- SHADOW: flattenSeq from Solution.lean, transliterated --------------------
def shadow_assemble(groups):
    """flattenSeq (groups) : List Int  ->  the in-order concatenation of every
    item's entries (empty items contribute [] and are skipped, not halted on).
    Mirrors `flattenSeq (g :: gs) = g ++ flattenSeq gs`, `flattenSeq [] = []`."""
    out = []
    for g in groups:          # front-recursive concatenation, left to right
        out = out + g
    return out


# --- ORACLE: the gold-patched assembly, transliterated verbatim ---------------
def oracle_assemble(groups):
    """patch.diff's behaviour: the patched get_traceback_frames assembly.

    `groups` is the chain in OUTPUT order (mapping.md §3.1: innermost first,
    matching the post-patch `exceptions.pop()` sequence). Each element is the
    output of the unchanged `get_exception_traceback_frames` for one exception
    — the carrier itself — so we `extend` directly on the element lists, exactly
    as the patched source does. We follow the patched control flow literally:
    pop the innermost (here: front of `groups`), extend, then loop the rest."""
    chain = list(groups)
    frames = []
    if not chain:
        # post-patch: with no exceptions, `get_traceback_frames` returns []
        # before reaching the assembly (the `if not exceptions: return frames`
        # guard). Modeled as the empty report.
        return frames
    exc_frames = chain.pop(0)                  # exc_value = exceptions.pop()
    frames.extend(exc_frames)                  # frames.extend(get_exception_...)
    while chain:                               # while exceptions:
        exc_frames = chain.pop(0)
        frames.extend(exc_frames)              # frames.extend(get_exception_...)
    return frames                              # return frames


# --- fuzzed chains ------------------------------------------------------------
def fuzz_inputs(n, rng):
    # Boundary cases first (plan §4.1 step 4): the discriminating shapes are
    # chains with empty items in every position (the pre-patch halt points).
    yield []                                   # no exceptions
    yield [[]]                                 # one exception, empty traceback
    yield [[1]]                                # one exception, one frame
    yield [[], [1]]                            # innermost empty (the F2P case)
    yield [[], [1, 2, 3]]
    yield [[1], []]                            # trailing empty
    yield [[], [], [7]]                        # leading empties then frames
    yield [[1], [], [2]]                       # empty in the middle
    yield [[1, 2], [3, 4], [5]]                # no empties
    yield [[], [], []]                         # all empty
    yield [[i] for i in range(10)]             # ten singletons

    for _ in range(n):
        k = rng.randint(0, 6)                  # chain length (# exceptions)
        chain = []
        for _ in range(k):
            m = rng.randint(0, 4)              # frames for this exception (may be 0)
            # distinct token range so dropped/duplicated runs are detectable
            chain.append([rng.randint(0, 50) for _ in range(m)])
        yield chain


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for groups in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_assemble(groups)
        oracle = oracle_assemble(groups)
        if shadow != oracle:
            disagreements.append((groups, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for g, sh, orc in disagreements:
            print("  groups=%r shadow=%r oracle=%r" % (g, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of assembleReport (flattenSeq) agrees with "
          "patch.diff's assembly behaviour on %d chains (seed=%d, incl. empty "
          "items in every position), 0 disagreements. No axioms."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
