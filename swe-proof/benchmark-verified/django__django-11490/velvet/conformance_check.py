#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-11490 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`SQLCompiler.get_combinator_sql` column push-down, exercised end-to-end by
actually evaluating a compound (`union`) queryset's `values_list(...)` against an
in-memory SQLite database — exactly the issue's reproduction.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule, transliterated to Python over the
              real repo types via the mapping.md §2 bijection:
                  persistent (shared carrier columns)  <->  the combined
                      sub-query's values_select (EMPTY for a fresh union member,
                      and — the whole point of the fix — kept empty across
                      evaluations because set_values runs on a clone)
                  outer                                <->  the projection the
                      outer values_list(...) requests
                  workingColumns(persistentOld, outer) =
                      outer if (persistentOld empty and outer non-empty) else
                      persistentOld
              So for every evaluation the predicted selected columns are exactly
              the requested `outer` columns, hence the predicted result row is
              tuple(row_value[c] for c in outer). There are NO A-tagged ops (no
              consumed axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched compound-SQL builder.
              We hold ONE shared compound queryset `qs1.union(qs1)` and evaluate
              `.values_list(*outer).get()` on it repeatedly with DIFFERENT column
              lists, reading back the real result tuple. (The bug is precisely
              that the shared combined sub-queries' columns leak across these
              repeated evaluations; the patched code clones, so each evaluation
              is free to pick its own columns.)

They must agree on every input. We ALSO assert the abstraction honesty guard:
after each evaluation the shared combined sub-queries' `values_select` is still
empty (the directive-5 frame `persistent = persistentOld`), confirming the
mapping.md §2 bijection.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. stdlib + django only; in-memory SQLite. Fuzz seed pinned
(mapping.md §4).
"""
import random
import sys

SEED = 11490
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

from django.db import connection, models  # noqa: E402  (after django.setup())


# A minimal stand-in for the issue's `ReservedName` model: two plain value
# columns so values_list() can project either, both, or just one. Defined at
# module top level so it is a real, ordinary model.
class Item(models.Model):
    name = models.CharField(max_length=20)
    order = models.IntegerField()

    class Meta:
        app_label = "auth"


def main():
    # Build the table for `Item` in the in-memory DB and insert one known row.
    with connection.schema_editor() as se:
        se.create_model(Item)
    Item.objects.create(name="a", order=2)
    ROW = {"name": "a", "order": 2, "id": Item.objects.get().id}

    # The columns the outer values_list(...) may project. (`id` included so the
    # projection space is more than the two business columns.)
    VALUE_COLS = ["name", "order", "id"]

    # The shared compound queryset — held across ALL evaluations, exactly like
    # the issue: qs1.union(qs1). Its combined sub-queries are the shared carriers
    # whose columns must NOT leak between evaluations.
    qs1 = Item.objects.all()
    compound = qs1.union(qs1)

    def combined_subquery_columns():
        """The shared carriers' current column projections (mapping.md §2:
        persistent <-> combined sub-query values_select)."""
        return [tuple(q.values_select) for q in compound.query.combined_queries]

    # --- the R/I shadow: Solution.lean workingColumns, transliterated ----------
    # workingColumns(carrier, outer) = outer if (carrier empty and outer
    # non-empty) else carrier.  The shared carriers stay empty across
    # evaluations (the fix), so for any non-empty outer the projected columns are
    # exactly `outer`, hence the predicted result tuple:
    def shadow_row(outer):
        return tuple(ROW[c] for c in outer)

    # --- the ORACLE: the REAL patched compound builder, end-to-end -------------
    def oracle_row(outer):
        """patch.diff behaviour: evaluate the SHARED compound queryset's
        values_list(*outer).get() and read back the real result tuple."""
        return compound.values_list(*outer).get()

    rng = random.Random(SEED)

    # Enumerate every non-empty ordered projection over VALUE_COLS as the
    # boundary sweep (covers the issue's ('name','order') then ('order') leak
    # case directly, in sequence on the shared queryset).
    def ordered_nonempty_projections(cols):
        out = []
        # single
        for c in cols:
            out.append((c,))
        # ordered pairs (distinct)
        for a in cols:
            for b in cols:
                if a != b:
                    out.append((a, b))
        # ordered triples (distinct) — full permutations
        for a in cols:
            for b in cols:
                for c in cols:
                    if len({a, b, c}) == 3:
                        out.append((a, b, c))
        return out

    boundary = ordered_nonempty_projections(VALUE_COLS)

    disagreements = []
    frame_violations = []
    count = 0

    def one_eval(outer):
        nonlocal count
        count += 1
        before = combined_subquery_columns()
        shadow = shadow_row(outer)
        oracle = oracle_row(outer)
        after = combined_subquery_columns()
        if shadow != oracle:
            disagreements.append((outer, shadow, oracle))
        # Directive-5 frame: the shared carriers must be unchanged (empty) before
        # AND after each evaluation. Any non-empty projection persisting on the
        # shared carriers is the bug the fix removes.
        if any(c for c in before) or any(c for c in after):
            frame_violations.append((outer, before, after))

    # Boundary sweep — in sequence on the SHARED compound queryset, so a leak
    # from one projection to the next would show as a disagreement.
    for outer in boundary:
        one_eval(outer)

    # Randomized fuzz to >= N_FUZZ: keep drawing ordered projections and
    # evaluating them on the SAME shared queryset.
    while count < N_FUZZ:
        k = rng.randint(1, len(VALUE_COLS))
        outer = tuple(rng.sample(VALUE_COLS, k))
        one_eval(outer)
        if len(disagreements) >= 10 and len(frame_violations) >= 10:
            break

    if disagreements or frame_violations:
        if disagreements:
            print(f"G-CONF FAIL: {len(disagreements)} R/I disagreement(s) over "
                  f"{count} evaluations (seed={SEED}):")
            for outer, sh, orc in disagreements[:10]:
                print(f"  outer={outer} shadow={sh} oracle={orc}")
        if frame_violations:
            print(f"G-CONF FAIL: {len(frame_violations)} shared-carrier frame "
                  f"violation(s) (shared sub-query columns leaked):")
            for outer, before, after in frame_violations[:10]:
                print(f"  outer={outer} before={before} after={after}")
        return 1

    print(f"G-CONF OK: R/I shadow of applyProjection agrees with patch.diff "
          f"behaviour on {count} repeated evaluations of one shared compound "
          f"queryset (seed={SEED}), 0 disagreements; shared combined sub-query "
          f"columns stayed empty across all evaluations (directive-5 frame held).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
