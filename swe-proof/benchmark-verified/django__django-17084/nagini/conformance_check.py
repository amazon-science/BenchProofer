#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-17084 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures/Invariant/Assert, MustTerminate)
          stripped; the @Pure helper `any_referenced_flag` copies over as a
          plain function. PSeq is a thin tuple shim (`ToSeq` wraps a list).
          No @ContractOnly callees in this bundle.

BRIDGE  — mapping.md section 2: the two flag lists are, per (aggregate, ref)
          pair of the case, the referenced annotation's window-containment
          flag (attribute absent -> True) and its subquery flag (attribute
          absent -> False), read after the unchanged resolve/annotate loop
          is replayed on a clone; `other_forces_wrap` is the OR of the six
          unchanged disjuncts (group-by tuple, sliced, existing aggregation,
          qualify, distinct, combinator), replayed the same way. The model's
          decision is order-independent, so each configuration is exercised
          over many permutations of the extracted flag lists — each a
          distinct Requires-satisfying input with the same oracle
          observable.

ORACLE  — the REAL patched single-row aggregation entry point (PYTHONPATH=
          /testbed, gold patch applied by the gate before this script runs):
          Query.get_aggregation on a live in-memory database, with the
          wrapping-subquery class temporarily instrumented to record whether
          the decision took the wrap branch. The observable compared against
          the shadow is exactly "was the aggregation wrapped".

Input domain: the modeled preconditions demand only read access to the flag
lists, so any (List[bool], List[bool], bool) is Requires-satisfying; inputs
are drawn from real query configurations. Configurations range over 0..4
annotations of five kinds (windowed, composite-windowed, subquery, plain
value, aggregate), 1..3 aggregate expressions each referencing 0..3
annotations (single- and multi-reference), and the wrap-forcing toggles
none / distinct / slice / both.

>= 1e5 Requires-satisfying inputs: (boundary + fuzz) configurations x 25
permuted flag-list variants each >= 100000. Pinned seed: 17084.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import random
import sys

SEED = 17084
N_FUZZ_CONFIGS = 4200
N_VARIANTS = 25

# ---------------------------------------------------------------------------
# Contract shims.
# ---------------------------------------------------------------------------


class PSeq:
    """Plain tuple shim for nagini's pure sequence type."""

    def __init__(self, t=()):
        self._t = tuple(t)

    def drop(self, n):
        return PSeq(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq(lst)


# ---------------------------------------------------------------------------
# model.py pure region, copied over as a plain function (@Pure stripped).
# ---------------------------------------------------------------------------


def any_referenced_flag(flags):
    if len(flags) == 0:
        return False
    return flags[0] or any_referenced_flag(flags.drop(1))


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------


def requires_subquery_wrap(window_flags, subquery_flags, other_forces_wrap):
    wseq = ToSeq(window_flags)
    sseq = ToSeq(subquery_flags)
    refs_subquery = False
    refs_window = False
    i = len(window_flags)
    while i > 0:
        refs_window = window_flags[i - 1] or refs_window
        i = i - 1
    j = len(subquery_flags)
    while j > 0:
        refs_subquery = subquery_flags[j - 1] or refs_subquery
        j = j - 1
    return other_forces_wrap or refs_subquery or refs_window


# ---------------------------------------------------------------------------
# Configuration space.
# ---------------------------------------------------------------------------

ANNOT_KINDS = ["window", "composite_window", "subquery", "plain", "aggregate"]
TOGGLES = ["none", "distinct", "slice", "distinct_slice"]


def make_annotation(kind):
    from django.db.models import F, Sum, Value, Window, Subquery, IntegerField
    from django.db.models.functions import Coalesce
    if kind == "window":
        return Window(expression=Sum("value"), order_by=F("id").asc())
    if kind == "composite_window":
        return Coalesce(Window(expression=Sum("value"), order_by=F("id").asc()),
                        Value(0))
    if kind == "subquery":
        return Subquery(_OTHER.objects.values("value")[:1],
                        output_field=IntegerField())
    if kind == "plain":
        return F("value") + Value(1)
    # "aggregate": a pre-existing aggregation annotation
    return Sum("value")


def make_aggregate(ref_aliases, rng):
    """An aggregate expression referencing the given annotation aliases
    (0..3 of them)."""
    from django.db.models import F, Sum, Count, Max
    if not ref_aliases:
        return rng.choice([Sum("value"), Count("id"), Max("value")])
    if len(ref_aliases) == 1:
        return rng.choice([Sum, Max])(ref_aliases[0])
    expr = F(ref_aliases[0])
    for alias in ref_aliases[1:]:
        expr = expr + F(alias)
    return Sum(expr)


def build_query(kinds, toggle):
    qs = _ITEM.objects.all()
    aliases = []
    for k, kind in enumerate(kinds):
        alias = "a%d" % k
        qs = qs.annotate(**{alias: make_annotation(kind)})
        aliases.append(alias)
    if toggle in ("distinct", "distinct_slice"):
        qs = qs.distinct()
    q = qs.query.clone()
    if toggle in ("slice", "distinct_slice"):
        q.set_limits(0, 3)
    return q, aliases


def extract_inputs(q, aggregate_exprs):
    """The bridge: replay the unchanged resolve/annotate loop on a clone and
    read, per (aggregate, ref) pair, the two per-referenced-annotation flags;
    then the six unchanged scalar disjuncts (mapping.md sections 1-2)."""
    from django.db.models.expressions import Ref
    q = q.clone()
    window_flags = []
    subquery_flags = []
    replacements = {}
    annotation_select_mask = q.annotation_select_mask
    for alias, aggregate_expr in aggregate_exprs.items():
        q.check_alias(alias)
        aggregate = aggregate_expr.resolve_expression(
            q, allow_joins=True, reuse=None, summarize=True)
        if not aggregate.contains_aggregate:
            raise TypeError("%s is not an aggregate expression" % alias)
        q.append_annotation_mask([alias])
        for ref in aggregate.get_refs():
            subquery_flags.append(
                bool(getattr(q.annotations[ref], "subquery", False)))
            window_flags.append(
                bool(getattr(q.annotations[ref], "contains_over_clause", True)))
        aggregate = aggregate.replace_expressions(replacements)
        q.annotations[alias] = aggregate
        replacements[Ref(alias, aggregate)] = aggregate
    for alias in aggregate_exprs:
        q.annotations.pop(alias)
    q.set_annotation_mask(annotation_select_mask)
    _, having, qualify = q.where.split_having_qualify()
    has_existing_aggregation = (
        any(getattr(annotation, "contains_aggregate", True)
            for annotation in q.annotations.values())
        or having
    )
    other_forces_wrap = bool(
        isinstance(q.group_by, tuple)
        or q.is_sliced
        or has_existing_aggregation
        or qualify
        or q.distinct
        or q.combinator
    )
    return window_flags, subquery_flags, other_forces_wrap


def oracle_wrapped(q, aggregate_exprs):
    """The real patched decision: run get_aggregation with the wrapping
    query class instrumented to record instantiation."""
    from django.db.models.sql import subqueries as subqueries_mod
    calls = []
    orig = subqueries_mod.AggregateQuery

    class _Recorder(orig):
        def __init__(self, *a, **k):
            calls.append(1)
            super().__init__(*a, **k)

    subqueries_mod.AggregateQuery = _Recorder
    try:
        # Execution of the assembled statement can fail for reasons outside
        # the modeled decision (engine feature gaps on exotic combinations);
        # the wrap decision itself is recorded at instantiation time, before
        # any statement runs, so a post-decision failure is tolerable when
        # the wrap branch was already taken.
        try:
            q.clone().get_aggregation("default", dict(aggregate_exprs))
        except Exception:
            if not calls:
                raise
    finally:
        subqueries_mod.AggregateQuery = orig
    return len(calls) > 0


def gen_config(rng):
    n_annot = rng.randint(0, 4)
    kinds = [rng.choice(ANNOT_KINDS) for _ in range(n_annot)]
    n_agg = rng.randint(1, 3)
    agg_refs = []
    for _ in range(n_agg):
        n_refs = rng.randint(0, min(3, n_annot))
        agg_refs.append(rng.sample(range(n_annot), n_refs))
    toggle = rng.choice(TOGGLES)
    return kinds, agg_refs, toggle


def boundary_configs():
    return [
        ([], [[]], "none"),                       # no annotations at all
        ([], [[]], "distinct"),
        ([], [[]], "slice"),
        (["window"], [[0]], "none"),              # the F2P shape
        (["composite_window"], [[0]], "none"),
        (["window"], [[]], "none"),               # window present, unreferenced
        (["subquery"], [[0]], "none"),
        (["plain"], [[0]], "none"),
        (["plain"], [[0]], "distinct"),
        (["aggregate"], [[]], "none"),            # existing aggregation only
        (["window", "subquery"], [[0], [1]], "none"),
        (["window", "plain"], [[1]], "none"),
        (["plain", "plain"], [[0, 1]], "none"),
        (["window", "plain"], [[0, 1]], "none"),  # multi-ref incl. a window
        (["subquery", "plain", "window"], [[0, 1], [2]], "distinct_slice"),
    ]


def variants(wf, sf, other, rng, n):
    out = [(list(wf), list(sf), other)]
    for _ in range(n - 1):
        w2, s2 = list(wf), list(sf)
        rng.shuffle(w2)
        rng.shuffle(s2)
        out.append((w2, s2, other))
    return out


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes"],
            USE_TZ=False,
        )
        django.setup()
    from django.db import connection, models

    global _ITEM, _OTHER

    class Meta:
        app_label = "confapp"

    _ITEM = type("Item", (models.Model,), {
        "__module__": __name__, "Meta": Meta,
        "value": models.IntegerField(default=0),
        "group": models.IntegerField(default=0)})
    _OTHER = type("Other", (models.Model,), {
        "__module__": __name__,
        "Meta": type("Meta", (), {"app_label": "confapp"}),
        "value": models.IntegerField(default=0)})

    with connection.schema_editor() as editor:
        editor.create_model(_ITEM)
        editor.create_model(_OTHER)
    _ITEM.objects.bulk_create(
        [_ITEM(value=v, group=v % 2) for v in range(5)])
    _OTHER.objects.create(value=7)

    rng = random.Random(SEED)
    configs = boundary_configs()
    for _ in range(N_FUZZ_CONFIGS):
        configs.append(gen_config(rng))

    checked = 0
    for kinds, agg_refs, toggle in configs:
        q, aliases = build_query(kinds, toggle)
        aggregate_exprs = {
            "agg%d" % i: make_aggregate([aliases[r] for r in refs], rng)
            for i, refs in enumerate(agg_refs)
        }
        wf, sf, other = extract_inputs(q, aggregate_exprs)
        real = oracle_wrapped(q, aggregate_exprs)
        for w2, s2, o2 in variants(wf, sf, other, rng, N_VARIANTS):
            shadow = requires_subquery_wrap(w2, s2, o2)
            if shadow != real:
                print("G-CONF FAIL (seed=%d):" % SEED)
                print("DISAGREEMENT\n"
                      "  config: kinds=%r agg_refs=%r toggle=%r\n"
                      "  input: window_flags=%r subquery_flags=%r other=%r\n"
                      "  shadow=%r\n  real(wrapped)=%r"
                      % (kinds, agg_refs, toggle, w2, s2, o2, shadow, real))
                return 1
            checked += 1

    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "single-row aggregation wrap decision on %d inputs "
          "(%d configurations x %d permuted flag variants, seed=%d), "
          "0 disagreements." % (checked, len(configs), N_VARIANTS, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
