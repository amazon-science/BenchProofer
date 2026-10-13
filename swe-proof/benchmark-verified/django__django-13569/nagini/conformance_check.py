#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13569 (nagini).

SHADOW: the impl regions of model.py `random_group_by_cols` and
`group_by_columns_for_ordering`, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The model IS Python:
the carriers are plain List[int]; the @Pure helpers (`offered_cols`,
`gathered`) are spec-only and are not needed by the executable shadow.
This bundle has no @ContractOnly callees.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`django.db.models.functions.Random.get_group_by_cols` (via a bare call and
via `OrderBy.get_group_by_cols` delegation) for the per-term contribution,
and the order-by gathering slice of `SQLCompiler.get_group_by`
(`for expr, (sql, params, is_ref) in order_by: if not is_ref:
expressions.extend(expr.get_group_by_cols())`) for the whole-list gather.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched modules importable. The loop slice is
mirrored literally here (it is a kind-I mirror per mapping.md section 1);
every per-term contribution inside it comes from the REAL expression's
`get_group_by_cols()`.

Type bridge (mapping.md section 2): an ordering-term list is carried as
three index-aligned List[int]:

    nondet[k] != 0  <->  term k's source is a non-deterministic ordering
                         expression (realized as a real `Random()`)
    ref[k]    != 0  <->  term k's order_by tuple has a truthy `is_ref`
    cols[k]         <->  the column identity a deterministic term offers
                         (realized as a real `RawSQL` leaf tagged with that
                         identity; each contributed expression object maps
                         back to its integer identity by object identity)

and a `get_group_by_cols()` result list maps to the List[int] of the
identities of its members, in order (empty list <-> []).

Input domain: the Requires demand only equal-length carriers (flags use the
`!= 0` truthy test, so any ints are admissible). Boundary: exhaustive term
lists of length 0..4 over every per-term shape (nondet in {0,1} x ref in
{0,1}) = 341 lists, plus non-canonical flag values and colid extremes.
Fuzz: 100_000 random term lists (length <= 8, flags drawn from truthy and
falsy non-canonical ints, colids across the int range) plus 1_000 direct
checks of the changed per-term function. Pinned fuzz seed: 13569.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13569
N_FUZZ = 100_000
N_DIRECT = 1_000


# --- the impl regions of model.py, verbatim, contract calls stripped ---------

def random_group_by_cols(colid):
    result = []  # type: ignore[var-annotated]
    return result


def group_by_columns_for_ordering(nondet, ref, cols):
    result = []  # type: ignore[var-annotated]
    i = len(nondet)
    while i > 0:
        if ref[i - 1] != 0:
            # A reference term offers nothing: gathered(tail j) == gathered(i).
            result = result
        elif nondet[i - 1] != 0:
            contributed = random_group_by_cols(cols[i - 1])
            result = contributed + result
        else:
            result = [cols[i - 1]] + result
        i = i - 1
    return result


# --- the differential check ---------------------------------------------------

def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()
    from django.db.models.functions import Random          # REAL patched callee
    from django.db.models.expressions import OrderBy, RawSQL

    # The order-by gathering slice of SQLCompiler.get_group_by, mirrored
    # literally (kind-I mirror); the per-term contribution is the REAL
    # expression's get_group_by_cols().
    def real_gather(order_by_terms):
        expressions = []
        for expr, is_ref in order_by_terms:
            if not is_ref:
                expressions.extend(expr.get_group_by_cols())
        return expressions

    def make_terms(nondet, ref, cols):
        """Realize the carrier triple as real ordering terms + an identity
        map from contributed expression object -> integer column identity."""
        terms = []
        ident_of = {}
        for nd, rf, cl in zip(nondet, ref, cols):
            if nd != 0:
                src = Random()
                # If a non-deterministic source ever contributed a column,
                # it would stand for its own term's identity.
                ident_of[id(src)] = cl
                expr = OrderBy(src)
            else:
                src = RawSQL('c%d' % cl, [])
                ident_of[id(src)] = cl
                expr = OrderBy(src)
            ident_of[id(expr)] = cl
            terms.append((expr, bool(rf)))
        return terms, ident_of

    checked = 0
    disagreements = 0

    def check_list(nondet, ref, cols):
        nonlocal checked, disagreements
        # Requires hold by construction: index-aligned, equal lengths.
        assert len(nondet) == len(ref) == len(cols)
        terms, ident_of = make_terms(nondet, ref, cols)
        real_exprs = real_gather(terms)
        real_idents = [ident_of.get(id(e), '<unmapped:%r>' % (e,))
                       for e in real_exprs]
        shadow = group_by_columns_for_ordering(nondet, ref, cols)
        checked += 1
        if real_idents != shadow:
            disagreements += 1
            print("DISAGREEMENT (whole-list gather)\n"
                  "  input: nondet=%r ref=%r cols=%r\n"
                  "  real  gathered identities = %r\n"
                  "  shadow                    = %r"
                  % (nondet, ref, cols, real_idents, shadow))
            return False
        return True

    def check_direct(colid):
        nonlocal checked, disagreements
        r = Random()
        real = r.get_group_by_cols()
        real_idents = [colid for _ in real]  # each member stands for its term
        shadow = random_group_by_cols(colid)
        checked += 1
        if real_idents != shadow:
            disagreements += 1
            print("DISAGREEMENT (per-term contribution)\n"
                  "  input: colid=%r\n"
                  "  real  Random().get_group_by_cols() -> %r (identities %r)\n"
                  "  shadow random_group_by_cols        -> %r"
                  % (colid, real, real_idents, shadow))
            return False
        return True

    # --- boundary: direct per-term checks over colid extremes ----------------
    for colid in (0, 1, -1, 2, 7, 10**9, -(10**9), 2**62):
        if not check_direct(colid):
            return 1

    # --- boundary: exhaustive term lists, length 0..4, all shapes ------------
    shapes = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (nondet, ref)
    n_boundary = 0

    def enum_lists(n, prefix):
        nonlocal n_boundary
        if n == 0:
            nondet = [s[0] for s in prefix]
            ref = [s[1] for s in prefix]
            cols = [k + 1 for k in range(len(prefix))]
            if not check_list(nondet, ref, cols):
                return False
            n_boundary += 1
            return True
        for s in shapes:
            if not enum_lists(n - 1, prefix + [s]):
                return False
        return True

    for n in range(0, 5):
        if not enum_lists(n, []):
            return 1

    # boundary: non-canonical truthy/falsy flags and colid extremes
    for nondet, ref, cols in [
        ([2], [0], [5]),
        ([-1], [0], [5]),
        ([0], [2], [5]),
        ([0], [-7], [5]),
        ([3, 0, -2], [0, -1, 0], [0, -(10**9), 10**9]),
        ([0, 0], [0, 0], [4, 4]),          # repeated identities
    ]:
        if not check_list(nondet, ref, cols):
            return 1
        n_boundary += 1

    # --- fuzz -----------------------------------------------------------------
    rng = random.Random(SEED)
    flag_pool = [0, 0, 0, 1, 1, 2, -1, 5, -100]
    for i in range(N_FUZZ):
        n = rng.randint(0, 8)
        nondet = [rng.choice(flag_pool) for _ in range(n)]
        ref = [rng.choice(flag_pool) for _ in range(n)]
        cols = [rng.randint(-10**6, 10**6) for _ in range(n)]
        if not check_list(nondet, ref, cols):
            return 1
        if i % (N_FUZZ // N_DIRECT) == 0:
            if not check_direct(rng.randint(-10**9, 10**9)):
                return 1

    print("G-CONF OK: shadow impl == real patched callees on %d inputs "
          "(%d boundary lists + 8 direct boundary + %d fuzz lists + %d "
          "direct fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, N_DIRECT, SEED))
    print(json.dumps({"checked": checked, "disagreements": disagreements,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
