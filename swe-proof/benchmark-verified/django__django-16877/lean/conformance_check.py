#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16877.

The bundle models ONE behavior: the `escapeseq` template filter (ADDED by the
patch in django/template/defaultfilters.py):

    @register.filter(is_safe=True)
    def escapeseq(value):
        return [conditional_escape(obj) for obj in value]

This script runs with the GOLD PATCH APPLIED in-container, so the REAL
`escapeseq` is the patched filter. We differential-test:

  * ORACLE  = the real, patched `escapeseq(value)`.
  * SHADOW  = the op-for-op transliteration of `implementation_escapeEach`
              (Solution.lean): build a result list by appending, in order, the
              per-element escaper applied to each element — with the escaper left
              as the REAL `conditional_escape` callee (the A-reference, per
              refinement.md — A legs keep the real repo callee in the shadow).

The bijection (mapping.md): the input sequence ↔ `List Elem`, each element either
an ordinary `str` (isSafe=false) or a `mark_safe(...)`/SafeString (isSafe=true);
the result `list[str]` ↔ `List String`. We compare oracle and shadow results
element-wise as plain strings (the SafeString-vs-str distinction is not part of
the modeled `List String` result, so we coerce both to `str`).

Inputs fuzzed: sequences of varying length whose elements mix
  * ordinary strings containing HTML metacharacters (& < > " '),
  * strings already marked safe via mark_safe.

stdlib-only (plus Django, present in the task image). Pinned seed: 16877.
"""
import random
import sys

SEED = 16877
N = 120_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
    django.setup()


def _result_key(res):
    """Normalize a filter result to a comparable key: a tuple of plain strings."""
    return tuple(str(x) for x in res)


def main() -> int:
    _setup_django()
    from django.template.defaultfilters import escapeseq
    from django.utils.html import conditional_escape
    from django.utils.safestring import mark_safe

    def oracle(seq):
        # The REAL patched escapeseq filter.
        return escapeseq(seq)

    def shadow(seq):
        # Transliteration of implementation_escapeEach: in-order accumulator
        # append of the per-element escaper, left as the REAL conditional_escape.
        acc = []
        for obj in seq:
            acc = acc + [conditional_escape(obj)]
        return acc

    def disagree(seq):
        g = _result_key(oracle(seq))
        s = _result_key(shadow(seq))
        if g != s:
            return (repr(seq), g, s)
        return None

    checked = 0

    # element generators -------------------------------------------------------
    raw_pool = ["", "x&y", "<p>", '"q"', "'a'", "a&b<c>d", "plain", "&amp;",
                "<script>", "líne\nbreak", "  ", "&<>\"'"]

    def make_raw(rng):
        return rng.choice(raw_pool)

    def make_safe(rng):
        return mark_safe(rng.choice(raw_pool))

    # --- boundary / edge cases ------------------------------------------------
    edge = [
        [],                                   # empty sequence
        ["x&y", "<p>"],                       # F2P test_basic (ordinary)
        [mark_safe("x&y"), mark_safe("<p>")], # F2P test_basic (already safe)
        ["x&y", "<p>", mark_safe("x&y"), mark_safe("<p>")],  # mixed
        [""],                                 # single empty string
        ["&<>\"'"],                           # all metacharacters
        [mark_safe("")],                      # safe empty
    ]
    for seq in edge:
        d = disagree(seq)
        if d:
            print(f"DISAGREE edge {d}")
            print("status=fail")
            return 1
        checked += 1

    # --- fuzz -----------------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N):
        ln = rng.randint(0, 6)
        seq = []
        for _ in range(ln):
            if rng.random() < 0.5:
                seq.append(make_raw(rng))
            else:
                seq.append(make_safe(rng))
        d = disagree(seq)
        if d:
            print(f"DISAGREE fuzz {d}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
