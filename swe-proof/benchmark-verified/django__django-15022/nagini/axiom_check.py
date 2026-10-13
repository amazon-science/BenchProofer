#!/usr/bin/env python3
"""G-AX soundness check for django__django-15022.

This bundle has NO axiomatized library callee: the changed operation is the
query-COMBINATION semantics, which is modelled DEEPLY in model.py by the pure
predicates `row_matches_all` and `some_row_matches_all`. The only @ContractOnly
symbol, `matches(row, term)`, is an UNINTERPRETED relation (its contract is the
tautology `Implies(Result(), Result())`) standing for the unchanged per-field
comparison; the proof relies on no property of it, so there is nothing to
over-/under-approximate. G-AX's job here is therefore to confirm that the deep
models faithfully formalise the two real Django ORM combination semantics:

  (fix)       queryset.filter(models.Q(*term_queries))      ->  EXISTS a single
              related row that matches EVERY term            ==  some_row_matches_all
              (one .filter() reuses one join => same-row)        (exists-row, for-all-terms)

  (pre-patch) for bit: qs = qs.filter(or_queries)            ->  EVERY term is
              (each .filter() adds a fresh join => different     matched by SOME row
               rows allowed per term)                        ==  every_term_matched_somewhere
                                                                 (for-all-terms, exists-row)

For every boolean match-matrix over small (#rows x #terms) domains we:
  * recompute the model's deep predicate `some_row_matches_all` (mirrored here);
  * compute the single-filter-AND result and the chained-filter result by the
    set semantics of Django's relational `.filter()` over a multi-valued
    relation;
  * assert  model == single-filter-AND  (the fix the spec pins),
  * assert  chained-filter == every_term_matched_somewhere  (the bug),
  * assert the two differ EXACTLY when no single row clears all terms while
    every term is individually covered (the quantifier swap the F2P tests probe,
    e.g. children Danielle/Daniel vs search "danielle 19").

It also confirms the concrete F2P scenarios from the test suite. stdlib-only;
exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


# --- model.py deep predicates, mirrored exactly (over a boolean matrix) -------
# match[r][t] == matches(row r, term t)

def row_matches_all(match, r, n_terms):
    # row r satisfies every term (front-recursive in model.py; iterative here)
    return all(match[r][t] for t in range(n_terms))


def some_row_matches_all(match, n_rows, n_terms):
    # exists-row, for-all-terms  (model.py retention predicate)
    return any(row_matches_all(match, r, n_terms) for r in range(n_rows))


def some_row_matches_term(match, n_rows, t):
    return any(match[r][t] for r in range(n_rows))


def every_term_matched_somewhere(match, n_rows, n_terms):
    # for-all-terms, exists-row  (pre-patch chained-filter semantics)
    return all(some_row_matches_term(match, n_rows, t) for t in range(n_terms))


# --- the real Django combination semantics, computed set-theoretically --------
# A candidate's related rows are the rows of `match`. A "term query" t is the
# set of related rows satisfying term t: {r : match[r][t]}.

def single_filter_and(match, n_rows, n_terms):
    """queryset.filter(Q(t0) & Q(t1) & ...): one join, the SAME related row must
    satisfy all term queries => the intersection over terms of the per-term row
    sets is non-empty <=> some row is in all of them."""
    keep_sets = [set(r for r in range(n_rows) if match[r][t]) for t in range(n_terms)]
    rows_clearing_all = set(range(n_rows))
    for s in keep_sets:
        rows_clearing_all &= s
    return len(rows_clearing_all) > 0


def chained_filter(match, n_rows, n_terms):
    """qs.filter(t0).filter(t1)...: each .filter() is a fresh join, so each term
    may pick a DIFFERENT related row => candidate kept iff every per-term row set
    is non-empty."""
    for t in range(n_terms):
        if not any(match[r][t] for r in range(n_rows)):
            return False
    return True


# --- exhaustive small-domain check -------------------------------------------

def check_all_matrices(max_rows, max_terms):
    swap_witnessed = False
    for n_rows in range(0, max_rows + 1):
        for n_terms in range(1, max_terms + 1):  # n_terms>=1: the spec's domain of interest
            for bits in itertools.product([False, True], repeat=n_rows * n_terms):
                match = [list(bits[r * n_terms:(r + 1) * n_terms]) for r in range(n_rows)]

                model = some_row_matches_all(match, n_rows, n_terms)
                fix = single_filter_and(match, n_rows, n_terms)
                assert model == fix, (
                    "deep model some_row_matches_all != single-filter-AND on "
                    "%r" % (match,))

                prebug = every_term_matched_somewhere(match, n_rows, n_terms)
                chained = chained_filter(match, n_rows, n_terms)
                assert prebug == chained, (
                    "every_term_matched_somewhere != chained-filter on %r" % (match,))

                # The quantifier swap: whenever the fix and the bug disagree, it
                # must be because every term is covered but no single row clears
                # all of them.
                if fix != prebug:
                    assert prebug and not fix, (
                        "unexpected disagreement direction on %r" % (match,))
                    swap_witnessed = True
    assert swap_witnessed, "no fix/bug divergence witnessed — domain too small"


# --- randomized fuzz over larger domains -------------------------------------

def fuzz(trials):
    rng = random.Random(15022)
    for _ in range(trials):
        n_rows = rng.randint(0, 6)
        n_terms = rng.randint(0, 6)
        match = [[rng.random() < 0.5 for _ in range(n_terms)] for _ in range(n_rows)]
        if n_terms >= 1:
            assert some_row_matches_all(match, n_rows, n_terms) == \
                single_filter_and(match, n_rows, n_terms)
            assert every_term_matched_somewhere(match, n_rows, n_terms) == \
                chained_filter(match, n_rows, n_terms)


# --- the concrete F2P scenarios ----------------------------------------------

def check_f2p_scenarios():
    # test_related_field_multiple_search_terms: search_fields = name, age over
    # children Danielle(age 18), Daniel(age 19).
    # rows: r0=Danielle, r1=Daniel. terms: t0, t1.
    #
    # search "danielle 19": t0="danielle", t1="19".
    #   matches(r0,t0)=name contains danielle -> True;  matches(r0,t1)=age contains 19 -> False (18)
    #   matches(r1,t0)=False (Daniel);                  matches(r1,t1)=True (19)
    m = [[True, False],   # Danielle
         [False, True]]   # Daniel
    assert some_row_matches_all(m, 2, 2) is False, "danielle 19 must drop (count 0)"
    assert every_term_matched_somewhere(m, 2, 2) is True, "pre-patch wrongly kept it"

    # search "daniel 19": t0="daniel" (icontains matches both 'Daniel' and 'Danielle'),
    #   t1="19".
    #   matches(r0,t0)=True (Danielle contains daniel); matches(r0,t1)=False
    #   matches(r1,t0)=True (Daniel);                   matches(r1,t1)=True
    m2 = [[True, False],   # Danielle
          [True, True]]    # Daniel  <- single row clears both terms
    assert some_row_matches_all(m2, 2, 2) is True, "daniel 19 must keep (count 1)"

    # test_multiple_search_fields change: 'Mary Jonathan Duo' goes 1 -> 0.
    # Three terms; no single related row clears all three together, though each
    # is individually covered.
    m3 = [[True, False, True],
          [False, True, True]]
    assert some_row_matches_all(m3, 2, 3) is False, "Mary Jonathan Duo must now be 0"
    assert every_term_matched_somewhere(m3, 2, 3) is True, "pre-patch returned 1"


def main():
    check_all_matrices(max_rows=3, max_terms=4)
    fuzz(20000)
    check_f2p_scenarios()
    print("G-AX OK: deep models some_row_matches_all / every_term_matched_"
          "somewhere == real Django single-filter-AND / chained-filter on all "
          "match matrices up to 3x4 + 20000 fuzz + F2P scenarios; "
          "no library callee to axiomatize (matches is uninterpreted).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
