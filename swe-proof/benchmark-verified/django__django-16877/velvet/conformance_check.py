#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16877 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (`List Elem` ↔ sequence of elements; `Elem ↔ ⟨list(str(obj)),
              hasattr(obj,"__html__")⟩`; `List Char` ↔ `str`). This is the
              element-wise list build `escSeq`/`condEscape`/`escapedSeq`. There
              are NO consumed axioms in this bundle, so the whole impl region is
              R/I (conf_skip=false).
  * ORACLE  — `patch.diff`'s behaviour: the patched filter `escapeseq` applied at
              base_commit (the real correctness oracle, G-RESOLVE), i.e.
              `[conditional_escape(obj) for obj in value]`.

They must agree on every input. Each element is fuzzed in BOTH a non-safe flavour
(plain str) and an already-safe flavour (mark_safe), since the per-element safe
flag is the discriminating behaviour. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 16877
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean entity/escapedSeq/condEscape/escSeq --------
_ENTITY = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
}


def shadow_escaped_seq(s):
    """escapedSeq: per-code-point HTML escape of a non-safe element."""
    return "".join(_ENTITY.get(ch, ch) for ch in s)


def shadow_cond_escape(chars, safe):
    """condEscape: a safe element passes through; else escape per code point."""
    return chars if safe else shadow_escaped_seq(chars)


def shadow_esc_seq(items):
    """escSeq: element-wise conditional escape, order-preserving. `items` is a
    list of (chars, safe) pairs — the Elem carrier (mapping.md §2)."""
    return [shadow_cond_escape(chars, safe) for (chars, safe) in items]


def oracle_esc_seq(items):
    """patch.diff's behaviour: the patched `escapeseq` filter. Build the real
    element objects (mark_safe for safe ones) and run the real filter."""
    from django.template.defaultfilters import escapeseq
    from django.utils.safestring import mark_safe
    value = [mark_safe(chars) if safe else chars for (chars, safe) in items]
    return [str(x) for x in escapeseq(value)]


def fuzz_sequences(n, rng):
    significant = list(_ENTITY.keys())
    ordinary = list("aZ0 ;#x39271quotlgmp") + ["é", "•"]
    alphabet = significant + ordinary

    def rand_str():
        k = rng.randint(0, 12)
        return "".join(rng.choice(alphabet) for _ in range(k))

    # boundary cases first (plan §4.1 step 4)
    yield []                                            # empty sequence
    # the exact F2P payloads, both flavours
    yield [("x&y", False), ("<p>", False)]              # test_basic list a
    yield [("x&y", True), ("<p>", True)]                # test_basic list b (safe)
    yield [("x&y", False), ("<p>", True)]               # mixed
    for c in significant:
        yield [(c, False)]
        yield [(c, True)]
        yield [(c + c, False)]
    yield [("".join(significant), False)]
    yield [("<script>alert('xss')</script>", False)]
    yield [("<script>alert('xss')</script>", True)]
    yield [("Joe's Crab Shack", False), ("Can't find my keys", True)]
    yield [("a&b<c>d\"e'f", False)]

    for _ in range(n):
        m = rng.randint(0, 5)
        items = [(rand_str(), bool(rng.getrandbits(1))) for _ in range(m)]
        yield items


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for items in fuzz_sequences(N_FUZZ, rng):
        count += 1
        shadow = shadow_esc_seq(items)
        oracle = oracle_esc_seq(items)
        if shadow != oracle:
            disagreements.append((items, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for it, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (it, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of escapeEach agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
