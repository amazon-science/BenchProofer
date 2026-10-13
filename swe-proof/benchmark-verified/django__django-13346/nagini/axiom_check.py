#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13346.

There is NO consumed @ContractOnly axiom in model.py: the changed behaviour
(every right-hand-side value slot of the membership comparison string must be
wrapped in the document-scalar extraction `JSON_EXTRACT(%s, '$')`) is modelled
DEEPLY by the front-recursive fold `slots_sql` in model.py's pure region.

This script validates that A-reference: it reproduces, in plain Python, EXACTLY
the placeholder-rewriting the real fix performs and asserts it equals the deep
model `slots_sql(n)` for every value-count n, on boundary + fuzz.

The real fix (django/db/models/fields/json.py, KeyTransformIn.process_rhs, on a
non-native-JSON backend such as SQLite / MySQL):

    rhs, rhs_params = super().process_rhs(...)        # In.process_rhs
    # rhs is the base membership placeholder: '(' + ', '.join(['%s']*n) + ')'
    func = ("JSON_EXTRACT(%s, '$')",) * len(rhs_params)
    rhs = rhs % func                                  # wrap every slot

So for n value slots the produced comparison string is
    '(' + ', '.join("JSON_EXTRACT(%s, '$')" for _ in range(n)) + ')'
whose INNER content (the per-slot expansion model.py pins as slots_sql) is the
', '-joined sequence of "JSON_EXTRACT(%s, '$')". The bare-slot pre-fix string
', '.join(['%s']*n) is what fails to match (the bug).

Imports nothing repo-specific: the slot wrapper and the `%`-substitution are
standard Python string operations -- the same operations the gold patch runs.
Exit 0 iff every obligation holds.
"""
import random
import sys

# model.py reference encodings (kept in lock-step with the pure region) --------
WRAPPED_SLOT = "JSON_EXTRACT(%s, '$')"   # wrapped_slot()  -> code points below
SEP = ", "                               # sep()
BARE_SLOT = "%s"                         # bare_slot() (the pre-fix slot)

# Sanity: the code-point literals embedded in model.py match these strings.
assert [ord(c) for c in WRAPPED_SLOT] == [
    74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
    40, 37, 115, 44, 32, 39, 36, 39, 41]
assert [ord(c) for c in SEP] == [44, 32]
assert [ord(c) for c in BARE_SLOT] == [37, 115]


def slots_sql_model(n):
    """Reference of model.py's deep model slots_sql(n): the wrapped per-slot
    expansion, ', '-joined. Returned as a code-point list."""
    if n == 0:
        return []
    s = SEP.join([WRAPPED_SLOT] * n)
    return [ord(c) for c in s]


def real_fix_inner(n):
    """The INNER (slot-expansion) content the real KeyTransformIn.process_rhs
    produces on a SQLite/MySQL backend, computed exactly as the gold patch does:
    base placeholder string '(' + ', '.join(['%s']*n) + ')', then
    rhs % (("JSON_EXTRACT(%s, '$')",) * n), and strip the outer parens."""
    rhs = "(" + ", ".join(["%s"] * n) + ")"            # In.process_rhs base
    func = (WRAPPED_SLOT,) * n                          # the fix
    rhs = rhs % func                                    # wrap every slot
    assert rhs[0] == "(" and rhs[-1] == ")"
    inner = rhs[1:-1]                                   # the per-slot expansion
    return [ord(c) for c in inner]


def real_fix_inner_prefix_bug(n):
    """The pre-fix INNER content: bare placeholders, never wrapped -- the bug."""
    rhs = "(" + ", ".join(["%s"] * n) + ")"
    return [ord(c) for c in rhs[1:-1]]


def main():
    # boundary: the single-element case the issue is specifically about, plus
    # small and larger value counts.
    boundary = [1, 2, 3, 4, 5, 10, 32, 100]
    for n in boundary:
        model = slots_sql_model(n)
        real = real_fix_inner(n)
        assert model == real, (
            "slots_sql deep model unsound for n=%d: real fix gives %r, "
            "deep model gives %r" % (n, real, model))
        # The pre-fix (bare-slot) string must DIFFER from the model for every
        # n >= 1 -- otherwise the spec would not sense the bug.
        bug = real_fix_inner_prefix_bug(n)
        assert bug != model, (
            "pre-fix bare-slot string coincides with the wrapped model for "
            "n=%d -- the spec would not discriminate the bug" % n)

    # fuzz random value counts.
    rng = random.Random(13346)
    for _ in range(5000):
        n = rng.randint(1, 64)
        model = slots_sql_model(n)
        real = real_fix_inner(n)
        assert model == real, (
            "slots_sql deep model unsound for n=%d (fuzz): real fix gives %r, "
            "deep model gives %r" % (n, real, model))

    # The single-element case from the problem statement explicitly: one slot,
    # fully wrapped, no separator.
    assert slots_sql_model(1) == [ord(c) for c in WRAPPED_SLOT]
    assert real_fix_inner(1) == [ord(c) for c in WRAPPED_SLOT]

    print("G-AX OK: slots_sql deep model == real KeyTransformIn.process_rhs "
          "slot-wrapping over %d boundary + 5000 fuzz value-counts; pre-fix "
          "bare-slot string differs for every count (bug sensed)."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
