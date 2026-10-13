#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11276 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch). The
              A-tagged callee `entityDecode` is NOT substituted by its axiom
              model here; G-CONF isolates the R/I legs, so the A leg is out of
              scope (it stays with G-AX). For THIS bundle the impl region's A
              content (entityDecode) appears only in the postconditions, not in
              the computed `out`, so the escape shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `django.utils.html.escape`
              applied at base_commit (the real correctness oracle, G-RESOLVE).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + hypothesis
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 11276
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean entity/escapedSeq, transliterated ---------
# entity (c : Char) : List Char  -- the per-code-point substitution (R/I ops)
_ENTITY = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
}


def shadow_escape(text):
    """escapedSeq (text.toList) transliterated to str, then mapping.md A4
    (mark_safe = identity on content). This is the R/I shadow of the impl."""
    # The backward `while` fold of escapeCodepoints computes exactly the
    # left-to-right per-code-point concatenation escapedSeq:
    return "".join(_ENTITY.get(ch, ch) for ch in text)


def oracle_escape(text):
    """patch.diff's behaviour: the patched django escape(). We resolve it from
    the repo at base_commit with the gold patch applied (the harness applies
    patch.diff before this runs); fall back to importing django if present."""
    from django.utils.html import escape  # patched: mark_safe(html.escape(str(text)))
    return str(escape(text))


def fuzz_inputs(n, rng):
    significant = list(_ENTITY.keys())
    ordinary = list("aZ0 ;#x39271quotlgmp") + ["é", "•"]
    alphabet = significant + ordinary
    # boundary cases first (plan §4.1 step 4)
    yield ""
    for c in significant:
        yield c
        yield c + c
    yield "".join(significant)
    yield "".join(reversed(significant))
    yield "a&b<c>d\"e'f"
    yield "x=1&amp;y=&lt;2&gt;"
    yield "<script>alert('xss')</script>"
    yield "Joe's Crab Shack"
    yield "Can't find my keys"
    yield "!$&'()*+,;=~:@,"
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_escape(s)
        oracle = oracle_escape(s)
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
    print("G-CONF OK: R/I shadow of escapeCodepoints agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
