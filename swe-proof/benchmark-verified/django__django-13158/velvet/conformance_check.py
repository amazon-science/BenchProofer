#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13158 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`Query.set_empty` (which now recurses into the combined sub-queries) and the
real `Query.clone` (which now deep-clones them), exercised end-to-end by
actually evaluating a set-combined (`union`) queryset and its `.none()` against
an in-memory SQLite database — exactly the issue's reproduction.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule, transliterated to Python over the
              real repo types via the mapping.md §2 bijection:
                  Combined.branches   <->  the operand querysets a combined
                      queryset is built from (`query.combined_queries`)
                  branchRows(b)       <->  the rows operand `b` contributes
                  combinedRows(bs)    <->  the rows the combined queryset yields
                  silenceAll          <->  set_empty recursing into every operand
              Solution.lean's `emptyCombined` guarantees, for ANY input:
                  combinedRows(silenceAll branches) = []      (the .none() result)
                  out.branches = silenceAll q.branches        (every operand
                      silenced; the INPUT `q` is read-only — directive-5 frame —
                      so the original combined queryset is unchanged).
              So the shadow predicts: `.none()` on the combined queryset yields
              the EMPTY set, while the original combined queryset still yields
              all of its rows. There are NO A-tagged ops (no consumed axioms),
              so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: hold ONE shared compound queryset
              `qs1.union(qs2)`; read its rows, then read `qs3.none()`'s rows,
              then re-read the shared queryset's rows. The bug is precisely that
              the pre-patch `.none()` (a) does not empty the operands so it
              returns ALL rows, and (b) without the clone would corrupt the
              shared operands. The patched code empties a CLONE's operands, so
              `.none()` is empty AND the original is untouched.

They must agree on every input. We ALSO assert the abstraction-honesty guard:
after each `.none()` the original combined queryset still yields its full row
set (the directive-5 frame `q` unchanged / the clone fix), confirming the
mapping.md §2 bijection.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. stdlib + django only; in-memory SQLite. Fuzz seed pinned
(mapping.md §4).
"""
import random
import sys

SEED = 13158
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


# A minimal stand-in for the issue's `Number` model: one integer value column we
# can filter on and read back. Defined at module top level so it is a real,
# ordinary model.
class Item(models.Model):
    num = models.IntegerField()

    class Meta:
        app_label = "auth"


def main():
    # Build the table and populate 0..9 (mirrors the issue's fixture).
    with connection.schema_editor() as se:
        se.create_model(Item)
    Item.objects.bulk_create(Item(num=i) for i in range(10))
    ALL_NUMS = list(range(10))

    def nums(qs):
        """The observable row set of a queryset, as a sorted list of `num`."""
        return sorted(o.num for o in qs)

    # --- the R/I shadow: Solution.lean's emptyCombined, transliterated ---------
    # branchRows(b) = [] if silenced else b.rows ; combinedRows = concat.
    # emptyCombined silences every branch, so the .none() result set is always
    # the empty list; and the input is read-only, so the original combined
    # queryset's rows are unchanged.
    def shadow_none_rows(branch_rowsets):
        # combinedRows(silenceAll branches) == [] for any branches.
        return []

    def shadow_combined_rows(branch_rowsets):
        # combinedRows(branches): concatenation of each operand's rows, then the
        # observable (set-semantics, sorted) row set.
        out = []
        for rs in branch_rowsets:
            out.extend(rs)
        return sorted(set(out))

    # All ordered pairs of disjoint, non-empty low/high splits of 0..9. Each
    # gives a union(qs1, qs2) whose operands contribute different row sets — the
    # boundary sweep covers the issue's exact (num<=1) | (num>=8) case.
    def split_cases():
        cases = []
        for lo in range(0, 9):          # qs1 = num <= lo  (rows 0..lo)
            for hi in range(lo + 1, 10):  # qs2 = num >= hi (rows hi..9)
                cases.append((lo, hi))
        return cases

    rng = random.Random(SEED)
    disagreements = []
    frame_violations = []
    count = 0

    def one_eval(lo, hi):
        nonlocal count
        count += 1
        qs1 = Item.objects.filter(num__lte=lo)
        qs2 = Item.objects.filter(num__gte=hi)
        qs3 = qs1.union(qs2)

        rows1 = [r for r in ALL_NUMS if r <= lo]
        rows2 = [r for r in ALL_NUMS if r >= hi]
        branch_rowsets = [rows1, rows2]

        # ORACLE: real .none() on the combined queryset, and the combined
        # queryset's own rows (read AFTER .none() to expose any aliasing leak).
        oracle_none = nums(qs3.none())
        oracle_combined = nums(qs3)

        # SHADOW predictions.
        sh_none = shadow_none_rows(branch_rowsets)
        sh_combined = shadow_combined_rows(branch_rowsets)

        if oracle_none != sh_none:
            disagreements.append(("none", (lo, hi), sh_none, oracle_none))
        if oracle_combined != sh_combined:
            disagreements.append(("combined", (lo, hi), sh_combined, oracle_combined))
        # Directive-5 frame / the clone fix: the original combined queryset must
        # still yield its full (unchanged) row set after .none() ran. A shrunken
        # row set here is the aliasing corruption the clone fix removes.
        if oracle_combined != sh_combined:
            frame_violations.append(((lo, hi), sh_combined, oracle_combined))

    # Boundary sweep — every disjoint low/high split.
    for lo, hi in split_cases():
        one_eval(lo, hi)

    # Randomized fuzz to >= N_FUZZ: redraw disjoint splits and re-run, each on a
    # fresh combined queryset built over the same shared table.
    while count < N_FUZZ:
        lo = rng.randint(0, 8)
        hi = rng.randint(lo + 1, 9)
        one_eval(lo, hi)
        if len(disagreements) >= 10:
            break

    if disagreements or frame_violations:
        if disagreements:
            print(f"G-CONF FAIL: {len(disagreements)} R/I disagreement(s) over "
                  f"{count} evaluations (seed={SEED}):")
            for kind, sp, sh, orc in disagreements[:10]:
                print(f"  {kind} split={sp} shadow={sh} oracle={orc}")
        if frame_violations:
            print(f"G-CONF FAIL: {len(frame_violations)} frame violation(s) "
                  f"(original combined queryset corrupted by .none()):")
            for sp, before, after in frame_violations[:10]:
                print(f"  split={sp} expected={before} got={after}")
        print("status=fail")
        return 1

    print(f"G-CONF OK: R/I shadow of emptyCombined agrees with patch.diff "
          f"behaviour on {count} union(.none()) evaluations (seed={SEED}); "
          f".none() always empty, and the original combined queryset kept its "
          f"full row set across all evaluations (directive-5 frame / clone held).")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
