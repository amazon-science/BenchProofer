#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15957 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`perGroupSlice`) is the net effect of the new helper
`_filter_prefetch_queryset` introduced by the patch in its sliced branch:

    def _filter_prefetch_queryset(queryset, field_name, instances):
        predicate = Q(**{f"{field_name}__in": instances})
        if queryset.query.is_sliced:
            low_mark, high_mark = queryset.query.low_mark, queryset.query.high_mark
            order_by = [expr for expr, _ in queryset.query.get_compiler(
                using=queryset._db or DEFAULT_DB_ALIAS).get_order_by()]
            window = Window(RowNumber(), partition_by=field_name, order_by=order_by)
            predicate &= GreaterThan(window, low_mark)
            if high_mark is not None:
                predicate &= LessThanOrEqual(window, high_mark)
            queryset.query.clear_limits()
        return queryset.filter(predicate)

The R/I shadow (`groupSlice`/`slicedGroups`) is a pure, input-dependent
computation, but the ORACLE it would be diffed against — `patch.diff`'s
behaviour — is observable ONLY by running this helper through the real ORM:

  * The result is produced by a SQL window query — `Window(RowNumber(),
    partition_by=field_name, order_by=order_by)` filtered to
    `low_mark < rn <= high_mark`, after `clear_limits()` — that materializes
    only against a live, window-function-capable database backend, inside the
    full `prefetch_related` pipeline (`RelatedManager` /
    `ManyRelatedManager.get_prefetch_queryset`, then the per-instance
    regrouping by `rel_obj_attr`).
  * There is no DB-free way to compute "what rows the patched queryset returns,
    grouped per instance" without standing up Django models + a DB + the
    prefetch machinery — i.e. re-running the F2P integration tests
    (PrefetchLimitTests.test_{foreignkey_reverse,m2m_forward,m2m_reverse,
    reverse_ordering}), which IS the real correctness oracle (G-RESOLVE). A
    pure transliteration cannot stand in for that backend execution.

Per SPEC_GUIDE §0 / LESSONS (conf_skip for DB-effect bundles; cf.
django-11179, django-13089), the soundness of the modeled net effect is carried
instead by G-VERIFY (the spec provably forces `out = slicedGroups low high
groups`), G-DIFF (the global-slice prepatch fails exactly that clause),
G-RESOLVE (the real patch resolves), and G-EQ / G-PANEL (the SQL-window ↔
per-group-slice correspondence narrative). See mapping.md §4 and refinement.md.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-15957 — the modeled do-block is "
          "the net effect of a SQL window-function prefetch filter "
          "(RowNumber() OVER (PARTITION BY field ORDER BY order_by), filtered "
          "to low_mark < rn <= high_mark) whose result materializes only "
          "against a live DB backend inside the prefetch_related pipeline; "
          "there is no DB-free, input-dependent R/I oracle to fuzz. "
          "conf_skip=true. Soundness covered by G-VERIFY + G-DIFF + G-RESOLVE "
          "+ G-EQ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
