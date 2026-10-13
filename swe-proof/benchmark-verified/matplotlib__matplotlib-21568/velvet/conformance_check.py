#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-21568.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch). The
              CHANGED op is the deep model `protectSeq` (R/I). The two A-tagged
              UNCHANGED context callees `reSub`/`removeEmpty` are NOT replaced by
              an axiom model — they are run as the REAL repo callees (`re.sub`
              with the repo pattern, and the real empty-group removal), exactly
              as G-CONF requires for A-tagged ops.
  * ORACLE  — `patch.diff`'s behaviour: the patched `_wrap_in_tex` applied at
              base_commit (the real correctness oracle, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 21568
N_FUZZ = 100_000

_RE_P = r'([a-zA-Z]+)'

# --- the R/I shadow: Solution.lean mathProtect/protectSeq, transliterated -----
# mathProtect (c : Char) : List Char  -- the per-code-point substitution (R/I)
_PROTECT = {
    "-": "{-}",
    ":": "{:}",
    " ": r"\;",
}


def shadow_wrap(text):
    """Solution.lean renderTexLabel, R/I shadow:
       reSub (REAL re.sub) -> protectSeq (deep model) -> concrete wrap ->
       removeEmpty (REAL empty-group removal)."""
    s = re.sub(_RE_P, r'}$\1$\\mathdefault{', text)        # A: real reSub
    protected = "".join(_PROTECT.get(ch, ch) for ch in s)  # R/I: protectSeq
    wrapped = '$\\mathdefault{' + protected + '}$'          # I: concrete wrap
    return wrapped.replace('$\\mathdefault{}$', '')         # A: real removeEmpty


def oracle_wrap(text):
    """patch.diff's behaviour: the patched matplotlib _wrap_in_tex(). The
    harness applies patch.diff before this runs."""
    from matplotlib.dates import _wrap_in_tex
    return _wrap_in_tex(text)


def fuzz_inputs(n, rng):
    significant = list(_PROTECT.keys())
    ordinary = list("aZ09;#x{}$\\<>\"'.Jan") + ["é", "•"]
    alphabet = significant + ordinary
    # boundary cases first
    yield ""
    for c in significant:
        yield c
        yield c + c
    yield "".join(significant)
    yield "".join(reversed(significant))
    # realistic post-formatter date/time labels the F2P tests feed in
    yield "1990"
    yield "1990-01-01"
    yield "01-01 20"
    yield "00:00:00"
    yield "01 00:10"
    yield "Jan 01 1990"
    yield "59.5"
    yield "Jan-01"
    yield "04:00"
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_wrap(s)
        oracle = oracle_wrap(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderTexLabel agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
