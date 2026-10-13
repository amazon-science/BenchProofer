#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15022 (plan §4.1).

Refutes the R/I refinement leg of the search-term combination decision modeled in
Solution.lean (`searchKeepsRow`, with the pure folds `anyRecord` / `conjTerms`).
There are NO axioms in this bundle: every op is pure boolean / list-fold logic over
free inputs, so the whole impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched combination logic instead of
running the real `queryset.filter(...)`:
  The patched `ModelAdmin.get_search_results` builds Django `Q` objects and calls
  `queryset.filter(models.Q(*term_queries))`, whose row-membership semantics over
  a *multi-valued relation* is realized by the SQL the ORM emits (a single JOIN
  with an AND of OR-clauses). Exercising the REAL filter requires a migrated DB, a
  registered ModelAdmin, a request, related rows, and the auth/admin stack — i.e.
  essentially the F2P Django test harness — purely to read back a kept/dropped
  boolean. That would not isolate the modeled decision. So, per the worker prompt,
  the ORACLE is the patched combination logic transliterated VERBATIM from the
  gold-patched django/contrib/admin/options.py:

      term_queries = []
      for bit in smart_split(search_term):           # -> the word list `terms`
          ...
          or_queries = Q(*((lookup, bit) ...), _connector=OR)  # -> matchTerm(r, t)
          term_queries.append(or_queries)
      queryset = queryset.filter(Q(*term_queries))   # AND of the per-word ORs

  Row membership of `queryset.filter(Q(*term_queries))` over a multi-valued
  relation: a candidate row is kept iff SOME related item satisfies the AND of all
  per-word OR-queries, i.e.
      keep_row = any( all( match(r, t) for t in terms ) for r in records )
  where `match(r, t)` is the UNCHANGED per-(item,word) OR-of-fields test, folded
  into the free input `matchTerm` (mapping.md §3). The pre-patch chained-filter
  semantics (kept iff every word is matched by *some*, possibly different, item)
  is the WRONG quantifier order and is NOT the oracle — the oracle is the patched
  ∃-item-∀-word membership.

  The SHADOW is the model from Solution.lean (`anyRecord` OR-fold of `conjTerms`
  AND-fold). We differential-test SHADOW vs ORACLE over exhaustive small cubes of
  the free inputs (every match bit-matrix for small |records| × |terms|) plus
  seeded fuzz over random match matrices and sizes. Exit 0 iff zero disagreements.
  stdlib only.
"""
import itertools
import random
import sys

SEED = 15022
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def conj_terms(match_of, terms):
    """`conjTerms` (front-recursive AND) transliterated: one related item matches
    every word. Empty word list -> True (vacuous)."""
    result = True
    for t in terms:
        result = result and match_of(t)
    return result


def any_record(match_term, terms, records):
    """`anyRecord` (front-recursive OR) transliterated: some related item matches
    all words. This is exactly what the backward `while` fold of `searchKeepsRow`
    accumulates. Empty item list -> False."""
    result = False
    for r in records:
        result = result or conj_terms(lambda t, r=r: match_term(r, t), terms)
    return result


def shadow_keep(records, terms, match_term):
    """searchKeepsRow post-image: result = anyRecord matchTerm terms records."""
    return any_record(match_term, terms, records)


# ---- ORACLE: patched django/contrib/admin/options.py transliterated -------

def oracle_keep(records, terms, match_term):
    """Row membership of `queryset.filter(models.Q(*term_queries))` over the
    related items: kept iff SOME related item matches the AND of all per-word
    OR-queries. `match_term(r, t)` is the unchanged per-(item,word) OR-of-fields
    test, folded per mapping.md §3."""
    return any(all(match_term(r, t) for t in terms) for r in records)


def make_match(matrix):
    """matrix[i][j] == does record i match term j. Returns matchTerm(r, t) on the
    integer identities r in range(len(records)), t in range(len(terms))."""
    def f(r, t):
        return bool(matrix[r][t])
    return f


def check(records, terms, match_term, disagreements):
    # Requires-satisfying inputs only: the modeled branch runs with >=1 word.
    if len(terms) == 0:
        return
    sh = shadow_keep(records, terms, match_term)
    orc = oracle_keep(records, terms, match_term)
    if sh != orc:
        disagreements.append((list(records), list(terms), sh, orc))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # --- exhaustive small cubes: every match bit-matrix for |records|<=3, ----
    # --- |terms| in 1..3. records/terms are integer identities. -------------
    for n_rec in range(0, 4):           # 0..3 related items
        for n_term in range(1, 4):      # 1..3 search words (Requires: >=1)
            records = list(range(n_rec))
            terms = list(range(n_term))
            cells = n_rec * n_term
            for bits in itertools.product([0, 1], repeat=cells):
                matrix = [list(bits[i * n_term:(i + 1) * n_term]) for i in range(n_rec)]
                check(records, terms, make_match(matrix), disagreements)
                count += 1
                if len(disagreements) >= 5:
                    break

    # --- seeded fuzz: random sizes + random match matrices -------------------
    for _ in range(N_FUZZ):
        n_rec = rng.randint(0, 6)
        n_term = rng.randint(1, 6)
        records = list(range(n_rec))
        terms = list(range(n_term))
        matrix = [[rng.randint(0, 1) for _ in range(n_term)] for _ in range(n_rec)]
        check(records, terms, make_match(matrix), disagreements)
        count += 1
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d checks:"
              % (len(disagreements), count))
        for rec, ts, sh, orc in disagreements:
            print("  records=%r terms=%r shadow=%r oracle=%r" % (rec, ts, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of searchKeepsRow (anyRecord/conjTerms folds) "
          "agrees with the patched options.py combination logic on %d checks "
          "(exhaustive small cubes + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
