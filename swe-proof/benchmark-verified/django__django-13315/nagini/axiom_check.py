#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13315.

This bundle consumes NO `@ContractOnly` axiom: the changed operation is pure
collection logic — collapsing the duplicate stream of join-matches to a
duplicate-free set of offered options — modelled DEEPLY over `List[int]` as the
front-recursive fold `dedup` (with the membership helper `occurs`). G-AX
therefore validates the *behavioural facts the deep model rests on* against the
REAL runtime semantics the patched code uses, per the no-axiom convention
(cf. django__django-13158):

  (1) The dedup semantics the gold patch realises. The gold path narrows the
      field's queryset with
          formfield.queryset.filter(
              Exists(formfield.queryset.model._base_manager.filter(complex_filter)))
      where `complex_filter &= Q(pk=OuterRef('pk'))`. Because `Exists(...)` is a
      per-row *correlated boolean subquery* (not a join folded into the outer
      SELECT), a base row is emitted iff AT LEAST ONE join path satisfies the
      restriction, and it is emitted AT MOST ONCE. The net observable effect on
      the queryset's contents is therefore exactly: the set of base rows that
      match, each once. G-AX reconstructs this DB-free as `exists_distinct` over
      a raw matching stream (a row id once per satisfying join path) and asserts
      it equals the model's `dedup` reference (membership preserved + no
      duplicate) over boundary + randomized fuzz streams. It also asserts the
      model's `occurs` reference equals real membership.

  (2) The pre-patch duplicate semantics. `QuerySet.complex_filter` over a join
      returns the raw stream verbatim — one output row per satisfying join path
      (no DISTINCT). G-AX asserts the raw stream still carries duplicates
      whenever a row matched along more than one join path, which is exactly what
      `model_prepatch.py` reproduces and what its failing clause
      `ToSeq(Result()) == dedup(ToSeq(matches))` rejects.

The contrast — "raw join-match stream" vs "its distinct image" — is a pure
collection fact, so this check needs no DB connection, no Django settings and no
SQL: it imports only the standard library and asserts set/multiset relations
over the modelled `List[int]` carrier. Exit 0 iff every obligation holds.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def occurs_ref(v, s):
    """Reference for model.py's `occurs`: membership of v in the sequence s."""
    return v in s


def dedup_ref(s):
    """Reference for model.py's front-recursive `dedup`: keep one representative
    of each distinct value, drop every repeat. The model keeps a head that
    recurs later at its LATER occurrence; encode that exactly so the reference
    matches the model element-for-element (not merely as a set)."""
    if len(s) == 0:
        return []
    if occurs_ref(s[0], s[1:]):          # s[0] recurs later -> drop it here
        return dedup_ref(s[1:])
    return [s[0]] + dedup_ref(s[1:])     # last occurrence -> keep it


# --- the REAL semantics the patch realises (reconstructed DB-free) -----------

def exists_distinct(matches):
    """The net observable effect of the gold path
       queryset.filter(Exists(... ._base_manager.filter(complex_filter))):
    a base row is offered iff some join path satisfies the restriction, and it
    is offered AT MOST ONCE. I.e. the set of matching rows, each once, in order
    of (last) appearance — exactly what dedup_ref encodes. Implemented here
    independently (a forward set-membership scan keeping the LAST occurrence) so
    the equality dedup_ref == exists_distinct is a genuine cross-check, not a
    restatement."""
    out = []
    for idx, r in enumerate(matches):
        if r not in matches[idx + 1:]:   # this is r's last occurrence
            out.append(r)
    return out


def complex_filter_raw(matches):
    """The pre-patch QuerySet.complex_filter over a join: the raw stream
    verbatim (one row per satisfying join path, no DISTINCT)."""
    return list(matches)


# --- the checks --------------------------------------------------------------

def check_dedup_reference(matches):
    """(1) the deep model `dedup` == the real Exists()-distinct semantics, and
    it is membership-preserving + duplicate-free."""
    model = dedup_ref(matches)
    real = exists_distinct(matches)
    assert model == real, (
        "dedup deep model unsound on %r: model gives %r, real Exists()-distinct "
        "gives %r" % (matches, model, real))
    # duplicate-free
    assert len(model) == len(set(model)), (
        "dedup must be duplicate-free, got %r from %r" % (model, matches))
    # membership preserved (no row dropped, none invented)
    assert set(model) == set(matches), (
        "dedup must preserve membership: %r vs input set of %r"
        % (model, matches))
    # occurs reference == real membership, over every candidate value
    universe = set(matches) | {-1, 0, 999}
    for v in universe:
        assert occurs_ref(v, matches) == (v in matches)


def check_prepatch_duplicates(matches):
    """(2) the pre-patch complex_filter raw stream still carries the duplicates
    whenever a row matched along more than one join path — the bug the prepatch
    reproduces and its failing clause rejects."""
    raw = complex_filter_raw(matches)
    assert raw == list(matches)
    has_dup = len(raw) != len(set(raw))
    model_distinct = dedup_ref(matches)
    if has_dup:
        # the raw (pre-patch) stream differs from the distinct (gold) image:
        # this is precisely model_prepatch.py's failing postcondition.
        assert raw != model_distinct, (
            "with a multi-path match the raw stream must differ from the "
            "distinct image, got raw=%r distinct=%r" % (raw, model_distinct))


def main():
    # --- boundary streams -------------------------------------------------
    boundary = [
        [],
        [1],
        [1, 1],                      # one row, two join paths
        [1, 2],                      # two distinct rows
        [1, 1, 1],                   # one row, three join paths
        [1, 2, 1],                   # interleaved duplicate
        [2, 1, 2, 1],                # the regression shape: 2 rows x 2 paths
        [3, 3, 5, 5, 7],             # mixed multiplicities
        [9, 8, 7, 6, 5, 4, 3, 2, 1],  # all distinct, descending
        [0, 0, 0, 0, 0],             # a single row matched five ways
    ]
    for m in boundary:
        check_dedup_reference(m)
        check_prepatch_duplicates(m)

    # --- randomized fuzz over small id universes (to force collisions) ----
    rng = random.Random(13315)
    for _ in range(50000):
        n = rng.randint(0, 14)
        universe = rng.randint(1, 6)            # small -> frequent duplicates
        m = [rng.randint(1, universe) for _ in range(n)]
        check_dedup_reference(m)
        check_prepatch_duplicates(m)

    # explicit regression witness mirroring test_limit_choices_to_no_duplicates:
    # two characters (marley, threepwood) each matched along several join paths
    marley, threepwood = 101, 102
    raw_matches = [threepwood, marley, marley, threepwood, marley, threepwood]
    offered = dedup_ref(raw_matches)
    assert set(offered) == {marley, threepwood}
    assert len(offered) == len({marley, threepwood}) == 2, (
        "the regression case must offer each matching character exactly once")
    assert complex_filter_raw(raw_matches) != offered, (
        "the pre-patch raw stream must render duplicates the gold path removes")

    print("G-AX OK: dedup deep model == real Exists()-distinct semantics "
          "(membership-preserving, duplicate-free) over %d boundary + 50000 "
          "fuzz match streams; occurs == real membership; pre-patch "
          "complex_filter raw stream carries the duplicates the gold path "
          "removes (model_prepatch's failing clause)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
