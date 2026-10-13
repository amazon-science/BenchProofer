#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-14351 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`In.get_group_by_cols(self, alias=None)` added by the patch (inherited by
`RelatedIn`).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. There are
NO A-tagged ops (no consumed axioms): the two delegated callees
`self.lhs.get_group_by_cols()` and `self.rhs.get_group_by_cols()` are FREE inputs
derived identically on both sides (mapping.md §3), so the shadow is pure R/I.

  * SHADOW  — Solution.lean's modeled rule, transliterated to Python over the real
              repo types via the mapping.md §2 bijection:
                  mustClamp        = rhsIsExpr and not rhsHasSelectFields
                  clampedSelect    = [pkCol] if mustClamp else selectOld
                  contributedCols  = lhsCols + rhsCols if rhsIsExpr else lhsCols
              with
                  rhsIsExpr          <-> hasattr(rhs, 'get_group_by_cols')
                  rhsHasSelectFields <-> getattr(rhs, 'has_select_fields', True)
                  lhsCols            <-> self.lhs.get_group_by_cols()
                  rhsCols            <-> self.rhs.get_group_by_cols()  (when expr)
                  pkCol              <-> the pk column add_fields(['pk']) installs
                  selectOld          <-> the rhs select clause on entry
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `In.get_group_by_cols`.

Per trial, ONE freshly built lookup is used. The SHADOW snapshot (entry select
clause, free inputs `lhsCols`/`rhsCols`) is taken first; reading those delegated
columns is non-mutating and idempotent (they are read-only observations the patch
forwards to), so the lookup remains in its entry state. The SHADOW then predicts
both observables. The ORACLE method is then invoked on the SAME lookup, and its
two observables are compared against the shadow's predictions:

  (1) the returned grouping columns — compared by EXACT OBJECT IDENTITY (same
      objects, since both sides read them off the same lookup); and
  (2) the rhs select-clause post-state — the `select` tuple and the
      `default_cols` flag. For a preserved select, identity-exact against the
      entry snapshot; for the clamp, structurally exactly one column with
      `default_cols=False` (the pk column the patch installs).

Object identity is the right observable (mapping.md §2): `Col` abstracts a column
by identity, `get_group_by_cols` returns the actual expression objects, and
`rhs.select` holds the actual column objects, all de-duplicated/emitted
downstream by identity.

Exit 0 iff zero disagreements over >=10^5 inputs; any disagreement is a
mechanical R/I-fidelity counterexample. No database rows are touched (the query
is built lazily and never evaluated). stdlib + django only. Fuzz seed pinned
(mapping.md §4).
"""
import random
import sys

SEED = 14351
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


_bootstrap_django()

from django.contrib.auth.models import User, Permission, Group  # noqa: E402
from django.db.models.lookups import In  # noqa: E402


def _find_in(node):
    """Locate the (Related)In lookup in a WhereNode tree."""
    for child in getattr(node, "children", []):
        if isinstance(child, In):
            return child
        if hasattr(child, "children"):
            r = _find_in(child)
            if r is not None:
                return r
    return None


def _build_lookup(field, rhs):
    """Build a fresh queryset filter `field__in=rhs` and return its In lookup."""
    qs = User.objects.filter(**{field + "__in": rhs})
    return _find_in(qs.query.where)


def _ids(cols):
    return tuple(id(c) for c in cols)


# ---- carriers: (label, field, rhs-builder) ---------------------------------
def _carriers():
    return [
        # subquery with NO explicit select fields -> clamp fires (the F2P case)
        ("sub_noselect_perm", "user_permissions",
         lambda: Permission.objects.all()),
        ("sub_noselect_perm_filter", "user_permissions",
         lambda: Permission.objects.filter(codename__startswith="a")),
        ("sub_noselect_group", "groups",
         lambda: Group.objects.all()),
        # subquery WITH explicit select fields (.values / values_list) -> no clamp
        ("sub_values_id", "user_permissions",
         lambda: Permission.objects.values("id")),
        ("sub_values_codename", "user_permissions",
         lambda: Permission.objects.values("codename")),
        ("sub_valueslist_pk", "user_permissions",
         lambda: Permission.objects.values_list("pk", flat=True)),
        ("sub_values_group", "groups",
         lambda: Group.objects.values("id")),
        # direct value list -> rhsIsExpr False -> lhs cols only, no clamp
        ("direct_list", "user_permissions", lambda: [1, 2, 3]),
        ("direct_list_one", "groups", lambda: [7]),
        ("direct_singleton", "user_permissions", lambda: [42]),
    ]


def _check_one(lk, alias):
    """Return None on agreement, else a (shadow, oracle) disagreement tuple."""
    rhs = lk.rhs
    rhs_is_expr = hasattr(rhs, "get_group_by_cols")

    # ---- SHADOW snapshot (entry state; reads are non-mutating) --------------
    lhs_cols = lk.lhs.get_group_by_cols()
    if rhs_is_expr:
        rhs_cols = rhs.get_group_by_cols()
        shadow_out = _ids(list(lhs_cols) + list(rhs_cols))   # contributedCols
        select_old = _ids(rhs.select)
        default_cols_old = getattr(rhs, "default_cols", None)
        has_select_fields = getattr(rhs, "has_select_fields", True)
        must_clamp = not has_select_fields
    else:
        shadow_out = _ids(list(lhs_cols))                    # lhs only
        select_old = None
        default_cols_old = None
        must_clamp = False

    # ---- ORACLE: the real patched method (mutates the rhs select clause) ----
    oracle_out = _ids(lk.get_group_by_cols(alias=alias))

    # (1) returned grouping columns: EXACT object identity.
    if shadow_out != oracle_out:
        return (("out", shadow_out), ("out", oracle_out))

    if not rhs_is_expr:
        return None  # no select clause to reconcile

    select_after = _ids(rhs.select)
    default_cols_after = getattr(rhs, "default_cols", None)

    # (2) rhs select-clause post-state.
    if must_clamp:
        # clampedSelect = [pkCol]: exactly one column installed, default_cols off.
        if len(select_after) != 1 or default_cols_after is not False:
            return (("clamp_to_1col_default_false",),
                    ("len", len(select_after), "default_cols", default_cols_after))
    else:
        # preserved: select unchanged (identity) and default_cols unchanged.
        if select_after != select_old or default_cols_after != default_cols_old:
            return (("preserve", select_old, "dc", default_cols_old),
                    ("got", select_after, "dc", default_cols_after))
    return None


def main():
    rng = random.Random(SEED)
    aliases = [None, "U0", "T5", "col_alias", ""]
    carriers = _carriers()

    # Exhaustive boundary sweep: every carrier x every alias, then fuzz.
    trials = [(lbl, fld, mk, a)
              for (lbl, fld, mk) in carriers for a in aliases]
    while len(trials) < N_FUZZ:
        lbl, fld, mk = carriers[rng.randrange(len(carriers))]
        trials.append((lbl, fld, mk, rng.choice(aliases)))

    disagreements = []
    count = 0
    for lbl, fld, mk, alias in trials:
        count += 1
        try:
            lk = _build_lookup(fld, mk())
            res = _check_one(lk, alias)
        except Exception as e:  # noqa: BLE001
            disagreements.append((lbl, alias, "CRASH:" + repr(e), None))
            if len(disagreements) >= 10:
                break
            continue
        if res is not None:
            disagreements.append((lbl, alias, res[0], res[1]))
            if len(disagreements) >= 10:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for lbl, a, sh, orc in disagreements[:10]:
            print("  carrier=%s alias=%r shadow=%s oracle=%s" % (lbl, a, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of inGroupByCols agrees with patch.diff "
          "behaviour through the real patched In.get_group_by_cols on %d inputs "
          "(seed=%d), 0 disagreements (subquery-no-select -> rhs select clamped "
          "to single pk column with default_cols=False; subquery-with-select / "
          "direct value list -> select preserved; contributed cols = lhs "
          "(+ rhs when expr), identity-exact)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
