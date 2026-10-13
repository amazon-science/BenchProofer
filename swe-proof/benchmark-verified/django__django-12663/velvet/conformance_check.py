#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-12663.

Refutes the R/I refinement leg (A2-A4: the modeled single-selection output-field
choice `source if source != 0 else field` over the integer-identity carrier).

ORACLE CHOICE — why we transliterate the source line instead of running
`Query.output_field`:
  The patched expression lives in `Query.output_field`, which requires a live
  `Query` with a populated `self.select` of real resolved `Col` expressions
  (a database connection, models, compiled columns). The behaviour under test is
  the pure choose-one-of-two: report the column's relation-aware `target` field
  when it is present and truthy, else the resolved `field`. So, per the worker
  prompt, the ORACLE is the patched source line transliterated VERBATIM:
      getattr(select, 'target', None) or select.field
  (from the gold-patched django/db/models/sql/query.py, `Query.output_field`,
  the `len(self.select) == 1` branch). The SHADOW is the modeled formula from
  Solution.lean's `outputFieldIdentity`. We differential-test SHADOW vs ORACLE
  over fuzzed integer-identity pairs (source, field) plus boundary cases under
  the bridge of mapping.md §2. Exit 0 iff zero disagreements. stdlib only.

BRIDGE (mapping.md §2):
  A field object is carried by its integer identity. `getattr(select,'target',
  None)` -> the source identity `source`, with `0` ≡ "attribute absent or
  falsy" (the `or` short-circuits to the fallback) and any nonzero ≡ a truthy,
  usable source field. `select.field` -> the resolved identity `field`, always
  nonzero (the require `sel.field != 0`). The ORACLE is run on a minimal stand-in
  object whose `target` truthiness and `field` are driven by these identities,
  so the Python `or` short-circuit is exercised exactly as in the real code.
"""
import random
import sys

SEED = 12663
N_FUZZ = 200_000
MAX_ID = 100_000


class _Sel:
    """Minimal stand-in for the single selected `Col`. `target` and `field` are
    modeled by integer identities (mapping.md §2). A `target` identity of 0
    models the attribute being absent/falsy: we set `target` to a falsy value
    (0) so Python's `getattr(..., 'target', None) or ...` short-circuits to the
    fallback exactly as the real `or` would for an absent/falsy `Col.target`."""

    def __init__(self, source, field):
        # source == 0 models "no usable source field": a falsy target attribute.
        # Using the int 0 (falsy) drives the real `or` short-circuit identically
        # to a missing attribute (getattr default None) -- both are falsy.
        self.target = source  # falsy iff source == 0
        self.field = field


def shadow(source, field):
    """outputFieldIdentity transliterated: the modeled output-field choice.
    Mirrors `if source ≠ 0 then return source else return sel.field` exactly."""
    if source != 0:
        return source
    return field


def oracle(source, field):
    """The patched source line, transliterated VERBATIM from
    django/db/models/sql/query.py (gold-patched Query.output_field):
        getattr(select, 'target', None) or select.field
    run on the integer-identity stand-in (mapping.md §2 bridge). Returns the
    truthy `target` identity, else falls back to the resolved `field`."""
    select = _Sel(source, field)
    return getattr(select, 'target', None) or select.field


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = []
    # Boundary cases: sentinel source (0); source == field (the no-explicit-
    # output_field case where the two notions coincide); source != field (the
    # discriminating nested-subquery regression); negative identities.
    for f in (1, 2, 7, MAX_ID):
        for s in (0, 1, f, f - 1, f + 1, -f, MAX_ID):
            cases.append((s, f))

    # Fuzz: field != 0 (the require); source any int incl. the 0 sentinel.
    for _ in range(N_FUZZ):
        f = rng.randint(1, MAX_ID)
        # bias toward the sentinel and toward source==field to stress both legs
        roll = rng.random()
        if roll < 0.2:
            s = 0
        elif roll < 0.4:
            s = f
        else:
            s = rng.randint(-MAX_ID, MAX_ID)
        cases.append((s, f))

    for source, field in cases:
        count += 1
        sh = shadow(source, field)
        o = oracle(source, field)
        if sh != o:
            disagreements.append((source, field, sh, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of outputFieldIdentity agrees with the patched "
          "source line `getattr(select, 'target', None) or select.field` on %d "
          "(source, field) identity pairs (boundary + fuzz, seed=%d, field!=0), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
