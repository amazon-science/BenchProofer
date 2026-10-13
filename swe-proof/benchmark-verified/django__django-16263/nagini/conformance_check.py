#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16263 (nagini).

WHAT IS BEING REFUTED
---------------------
model.py models the two decisions the gold patch installs in
``Query.get_aggregation`` (mapping.md section 1):

  * ``existing_summary_forces_derived(selected, summ, filter_summary)`` -- the
    ``has_existing_aggregation`` computation at ``django/db/models/sql/query.py``
    (post-patch body lines ~444-456), consumed by the ``if (... or
    has_existing_aggregation or ...)`` that decides the wrapping subquery;
  * ``inner_column_kept(alias, added, ref_tree)`` -- the inner-query
    ``annotation_mask`` construction (post-patch ``annotation_mask = set(); for
    name in added_aggregate_names: annotation_mask.add(name); annotation_mask |=
    inner_query.annotations[name].get_refs(); inner_query.set_annotation_mask(
    annotation_mask)``).

SHADOW
------
The ``# impl-start`` / ``# impl-end`` regions of BOTH model.py functions, copied
VERBATIM with only the contract calls removed (``Requires`` / ``Ensures`` /
``Invariant`` / ``Assert`` / ``MustTerminate`` and the ``# invariants-start`` /
``-end`` markers). Nothing is restructured, renamed or simplified: the two
backward ``while`` scans, the ``tail_refs`` / ``cons`` intermediate assignments
inside ``inner_column_kept``'s second loop, and the ``found or filter_summary !=
0`` return are the model's own statements. The three ``@Pure`` helpers
(``collect_refs``, ``any_selected_summary``, ``seq_contains``) are copied
verbatim too, front-recursion and all, on top of a small immutable ``PSeq`` shim
(``take`` / ``drop`` / ``+`` / ``len`` / ``[]`` / ``==``; ``ToSeq`` materialises
one from a list). ``collect_refs`` is genuinely EXECUTED by the shadow (the
impl region's own ``tail_refs = collect_refs(ToSeq(ref_tree).drop(j))`` line);
the other two are used only for the internal spec cross-check below, mirroring
the model's ``Ensures``. There are no ``@ContractOnly`` callees in this bundle
(mapping.md section 3: no consumed axioms).

ORACLE -- the REAL patched repo function, CALLED, not transliterated
-------------------------------------------------------------------
Unlike the velvet and lean siblings (whose docstrings record a transliteration
of the patched decision lines because a Lean/velvet shadow cannot call Python),
this check DRIVES the real patched ``Query.get_aggregation`` in-container: the
gate applies patch.diff to /testbed and runs with ``PYTHONPATH=/testbed``, so a
real ``django.db.models.sql.query.Query`` over a real model, a real sqlite
connection and real resolved annotations executes the patched code path for
every probe. The real ``Ref.get_refs`` / ``BaseExpression.get_refs`` /
``WhereNode.get_refs`` (also added by the patch) are what build the real mask,
so the deep model ``collect_refs`` is exercised against the real gatherer here
as well, not assumed.

Two observables are read off the real run:

  * DERIVED FORM (decision 1): whether ``get_aggregation`` constructed an
    ``AggregateQuery`` (i.e. took the wrapping-subquery branch). Every probe
    pins the other four disjuncts of that ``if`` to false and ASSERTS it
    (``isinstance(group_by, tuple)`` / ``is_sliced`` / ``distinct`` /
    ``combinator``), so the branch taken is exactly
    ``has_existing_aggregation``. The real local
    ``has_existing_aggregation`` is additionally captured by frame inspection
    whenever the patched code reaches a ``set_annotation_mask`` call inside
    ``get_aggregation``, and cross-checked against the branch observable.
  * INNER MASK (decision 2): the real ``annotation_mask`` set object, captured
    by identity at the patched ``inner_query.set_annotation_mask(
    annotation_mask)`` call site. Membership of every alias in a fixed name
    universe (all pre-existing aliases, the pushed-out summary names, and two
    never-annotated ghost names) is compared against the shadow's verdict.
    Decision 2 is only in scope when the derived form was taken, which is what
    model.py specifies, so the mask comparison runs exactly on those probes.

A probe that raises after both observables are captured (a phantom ``Ref`` makes
the emitted SQL unparsable, for instance) is still compared -- the decisions are
made before execution. A probe that fails BEFORE the decision was reached is a
hard error, never a silent skip.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
Every bit of the model's carriers is READ OFF the real objects, never assumed:

  * ``selected[k] != 0``  <=  ``alias_k in query.annotation_select`` (built by
    ``add_annotation(..., select=True)``, i.e. what ``annotate()`` does;
    ``select=False`` is what ``alias()`` does);
  * ``summ[k] != 0``      <=  ``getattr(ann, "contains_aggregate", True) or
    getattr(ann, "contains_over_clause", True)`` on the RESOLVED annotation;
  * ``filter_summary != 0`` <= ``any(query.where.split_having_qualify()[1:])``
    evaluated by the real ``WhereNode``;
  * ``added``            <=  the pushed-out summary names, as alias codes;
  * ``ref_tree``         <=  the resolved added annotations flattened by the
    bridge of mapping.md section 2: a ``Ref`` is a LEAF contributing the
    positive code of its ``refs`` and its source is NOT descended into, any
    other node contributes ``0`` and then its children (for several added names
    the flattens are joined under one composite ``0`` node -- ``collect_refs``
    of a concatenation is the concatenation of the ``collect_refs``, which is
    exactly the real union over ``added_aggregate_names``);
  * an alias string <=> a stable positive ``int`` code (index in ``NAME_POOL``
    + 1; ``0`` is reserved by the carrier for a non-referencing node).

INPUTS (>= 1e5 satisfying the Requires)
---------------------------------------
The Requires are only permission/length side conditions
(``len(selected) == len(summ)``, plus ``MustTerminate``), and the bridge
constructs the two carriers in lock-step from one annotation list, so every
generated probe satisfies them by construction. 44 boundary probes run first --
empty carrier, singleton selected/unselected x aggregate/non-aggregate, the
three FAIL_TO_PASS shapes and the referenced-kept control, a HAVING filter, a
QUALIFY (window) filter, a selected window annotation, refs to unselected
aliases, phantom refs, two pushed-out summary names, deep/wide reference trees --
covering every branch of both impl regions (``found`` set and not set;
``filter_summary`` alone forcing the derived form; ``in_added`` true and false;
``in_refs`` true and false; ``node == 0`` and ``node != 0`` in the reference
scan). Seeded fuzz then fills the count to 100000 probes. Each probe yields one
decision-1 comparison plus, when the derived form was taken, one decision-2
comparison per name in the universe (~9), so ~1e5 probes carry ~5e5
shadow-vs-real comparisons.

Pinned seed: 16263 (recorded in mapping.md section G-CONF).
Exit 0 iff zero disagreements; on a disagreement the probe, both outputs and the
observable are printed and the exit status is 1. stdlib + Django only.

NEGATIVE CONTROLS (this check is capable of failing; run during construction)
----------------------------------------------------------------------------
  * shadow mutated to the PRE-patch decision-1 source (drop the ``selected``
    conjunct, ``if s != 0 and m != 0`` -> ``if m != 0``): FAILS -- an alias-only
    aggregate no longer forces the derived form in the real code.
  * shadow mutated to the pre-patch predicate (``if True``, annotation
    truthiness): FAILS.
  * shadow mutated to the PRE-patch decision-2 (``return in_added or in_refs``
    -> ``return True``, i.e. the unconditional
    ``set_annotation_mask(self.annotation_select)``): FAILS -- the real mask
    prunes.
  * ``filter_summary`` disjunct dropped from the decision-1 return: FAILS.
  * the reference scan's hit disabled (``if node != 0 and node == alias`` ->
    ``if False``): FAILS -- a referenced alias is really kept.
  * run against the UNPATCHED ``get_aggregation``: exits non-zero
    (``status=error``), never a silent pass -- the observables are the patched
    locals, so their absence is reported rather than scored as "no wrapping".
"""
import json
import os
import random
import sys

SEED = 16263
N_PROBES = 100_000

# Alias universe: code = index + 1 (0 is reserved by the carrier for a
# non-referencing node). "ghost1"/"ghost2" are never annotated -- they exist so
# a Ref can point at a name the query does not carry.
NAME_POOL = [
    "exa0", "exa1", "exa2", "exa3", "hfilter", "qfilter",
    "__count", "avg2", "ghost1", "ghost2",
]
CODE = {n: i + 1 for i, n in enumerate(NAME_POOL)}
NAME = {c: n for n, c in CODE.items()}
EXISTING_NAMES = ["exa0", "exa1", "exa2", "exa3"]
ADDED_NAMES = ["__count", "avg2"]


# ---------------------------------------------------------------------------
# PSeq shim: the Nagini carrier, immutable, with the operations model.py uses.
# ---------------------------------------------------------------------------
class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# pure region of model.py, copied verbatim (contracts/decorators stripped)
# ---------------------------------------------------------------------------
def any_selected_summary(selected, summ):
    if len(selected) == 0 or len(summ) == 0:
        return False
    return (selected[0] != 0 and summ[0] != 0) or any_selected_summary(
        selected.drop(1), summ.drop(1)
    )


def collect_refs(tree):
    if len(tree) == 0:
        return PSeq(0).take(0)
    if tree[0] != 0:
        return PSeq(tree[0]) + collect_refs(tree.drop(1))
    return collect_refs(tree.drop(1))


def seq_contains(s, x):
    if len(s) == 0:
        return False
    return s[0] == x or seq_contains(s.drop(1), x)


# ---------------------------------------------------------------------------
# impl region of model.py, copied VERBATIM with only contract calls removed
# ---------------------------------------------------------------------------
def existing_summary_forces_derived(selected, summ, filter_summary):
    # impl-start
    found = False
    i = len(selected)
    while i > 0:
        s = selected[i - 1]
        m = summ[i - 1]
        if s != 0 and m != 0:
            found = True
        i = i - 1
    return found or filter_summary != 0
    # impl-end


def inner_column_kept(alias, added, ref_tree):
    # impl-start
    in_added = False
    i = len(added)
    while i > 0:
        c = added[i - 1]
        if c == alias:
            in_added = True
        i = i - 1
    in_refs = False
    j = len(ref_tree)
    while j > 0:
        node = ref_tree[j - 1]
        if node != 0:
            tail_refs = collect_refs(ToSeq(ref_tree).drop(j))  # type: PSeq[int]
            cons = PSeq(node) + tail_refs  # type: PSeq[int]
        if node != 0 and node == alias:
            in_refs = True
        j = j - 1
    return in_added or in_refs
    # impl-end


# ---------------------------------------------------------------------------
# real repo side: setup + observation spies
# ---------------------------------------------------------------------------
OBS = {}


def _setup_django():
    if os.path.isdir("/testbed"):
        sys.path.insert(0, "/testbed")
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


def _install_spies():
    """Observe the patched get_aggregation's two decisions.

    * ``AggregateQuery.__init__`` firing  == the wrapping-subquery branch taken.
    * ``Query.set_annotation_mask`` called from ``get_aggregation`` with the
      patched local ``annotation_mask`` object == the inner mask; the same frame
      yields the real ``has_existing_aggregation`` local.
    * "the decision was actually reached" (a probe that dies EARLIER must never
      be scored as "no wrapping"): either the real
      ``has_existing_aggregation`` local was captured, or
      ``WhereNode.split_having_qualify`` was called from ``get_aggregation``.
      That disjunction is total. ``has_existing_aggregation = any(<selected
      annotations>) or any(self.where.split_having_qualify()[1:])``
      short-circuits, so ``split_having_qualify`` is skipped exactly when the
      first ``any`` is already true -- and then the wrapping branch runs, whose
      first statement block always calls
      ``inner_query.set_annotation_mask(self.annotation_select)`` from the
      ``get_aggregation`` frame, capturing the local. Conversely, whenever the
      first ``any`` is false the ``or`` evaluates
      ``split_having_qualify()``. So every completed decision sets at least one
      of the two.
    """
    import django.db.models.sql.subqueries as subqueries
    from django.db.models.sql.query import Query
    from django.db.models.sql.where import WhereNode

    real_aggregate_query = subqueries.AggregateQuery

    class SpyAggregateQuery(real_aggregate_query):
        def __init__(self, *a, **kw):
            OBS["wrapped"] = True
            super().__init__(*a, **kw)

    subqueries.AggregateQuery = SpyAggregateQuery

    real_split = WhereNode.split_having_qualify

    def spy_split(self, *a, **kw):
        if sys._getframe(1).f_code.co_name == "get_aggregation":
            OBS["decided"] = True
        return real_split(self, *a, **kw)

    WhereNode.split_having_qualify = spy_split

    real_set_mask = Query.set_annotation_mask

    def spy_set_mask(self, names):
        frame = sys._getframe(1)
        if frame.f_code.co_name == "get_aggregation":
            loc = frame.f_locals
            if "has_existing_aggregation" in loc:
                OBS.setdefault("has_existing_aggregation",
                               bool(loc["has_existing_aggregation"]))
            mask = loc.get("annotation_mask")
            if mask is not None and mask is names:
                OBS["mask"] = set(names)
        return real_set_mask(self, names)

    Query.set_annotation_mask = spy_set_mask


# ---------------------------------------------------------------------------
# expression trees: model form -> real Django expression -> carrier flatten
# ---------------------------------------------------------------------------
# A model tree node is ('ref', name) | ('comp', [children]) | ('val',).

def build_real(node, mods):
    Ref, Value, Func, ExpressionWrapper, IntegerField = mods
    kind = node[0]
    if kind == "ref":
        # The Ref's source is a plain Value: the model's flatten treats a Ref as
        # a LEAF (matching Ref.get_refs() == {self.refs}), and nested-Ref-source
        # fidelity is G-AX's business; here sources stay simple so the emitted
        # SQL of a kept reference remains well formed.
        return Ref(node[1], Value(1))
    if kind == "val":
        return Value(1)
    children = [build_real(c, mods) for c in node[1]]
    if not children:
        return Value(1)
    if len(children) == 1:
        return ExpressionWrapper(children[0], output_field=IntegerField())
    return Func(*children, function="COALESCE")


def flatten_expr(expr, Ref):
    """mapping.md section 2: a Ref is a LEAF contributing its referent's code
    (its source is NOT descended into); any other node contributes 0 and then
    its folded children."""
    if isinstance(expr, Ref):
        return [CODE[expr.refs]]
    out = [0]
    getter = getattr(expr, "get_source_expressions", None)
    if getter is not None:
        for sub in getter():
            if sub is not None:
                out.extend(flatten_expr(sub, Ref))
    return out


# ---------------------------------------------------------------------------
# one probe: build the real query, run the real patched decision, diff
# ---------------------------------------------------------------------------
class ProbeError(Exception):
    pass


def run_probe(spec, ctx):
    """spec = {
        'existing': [(alias, kind)]  kind in {'agg','plain','window'} x selected,
        'filter': None|'having'|'qualify',
        'added': [(alias, agg_kind, tree)],
       }
    Returns an error string on disagreement, else None."""
    (Query, Count, Lower, Sum, Avg, Window, RowNumber, Q, Ref, Value, Func,
     ExpressionWrapper, IntegerField, model) = ctx
    mods = (Ref, Value, Func, ExpressionWrapper, IntegerField)

    q = Query(model)
    existing_aliases = []
    for alias, kind, selected in spec["existing"]:
        if kind == "agg":
            expr = Count("num")
        elif kind == "window":
            expr = Window(RowNumber())
        else:
            expr = Lower("name")
        q.add_annotation(expr, alias, select=bool(selected))
        existing_aliases.append(alias)
    if spec["filter"] == "having":
        q.add_annotation(Count("num"), "hfilter", select=False)
        q.add_q(Q(hfilter__gt=0))
        existing_aliases.append("hfilter")
    elif spec["filter"] == "qualify":
        q.add_annotation(Window(RowNumber()), "qfilter", select=False)
        q.add_q(Q(qfilter__gt=0))
        existing_aliases.append("qfilter")

    # --- bridge, forward: read the model's carriers OFF the real query -------
    selected = []
    summ = []
    for alias in existing_aliases:
        ann = q.annotations[alias]
        selected.append(1 if alias in q.annotation_select else 0)
        summ.append(1 if (getattr(ann, "contains_aggregate", True)
                          or getattr(ann, "contains_over_clause", True)) else 0)
    filter_summary = 1 if any(q.where.split_having_qualify()[1:]) else 0

    added_names = []
    ref_tree = [0]
    for alias, agg_kind, tree in spec["added"]:
        if tree[0] == "count":
            # Count("*") is the summary `get_count()` itself pushes out; its
            # get_refs() is empty.
            expr = Count("*")
        else:
            inner = build_real(tree, mods)
            expr = Sum(inner) if agg_kind == "sum" else Avg(inner)
        q.add_annotation(expr, alias, is_summary=True)
        added_names.append(alias)
        ref_tree.extend(flatten_expr(q.annotations[alias], Ref))
    added = [CODE[n] for n in added_names]

    # The four other disjuncts of the patched `if` must be false, so that the
    # branch taken IS has_existing_aggregation (the modelled decision).
    if (isinstance(q.group_by, tuple) or q.is_sliced or q.distinct
            or q.combinator):
        raise ProbeError("probe left an out-of-scope subquery trigger set: "
                         "group_by=%r is_sliced=%r distinct=%r combinator=%r"
                         % (q.group_by, q.is_sliced, q.distinct, q.combinator))

    # --- run the REAL patched get_aggregation --------------------------------
    OBS.clear()
    OBS["wrapped"] = False
    real_error = None
    try:
        q.get_aggregation("default", list(added_names))
    except Exception as exc:               # noqa: BLE001 - see docstring
        real_error = "%s: %s" % (type(exc).__name__, exc)
    if not (OBS.get("decided")
            or OBS.get("has_existing_aggregation") is not None):
        raise ProbeError("real get_aggregation never reached the decision "
                         "(error=%r)" % (real_error,))

    # --- decision 1 ---------------------------------------------------------
    shadow_derived = existing_summary_forces_derived(selected, summ,
                                                     filter_summary)
    real_derived = bool(OBS["wrapped"])
    captured = OBS.get("has_existing_aggregation")
    if captured is not None and captured != real_derived:
        return ("OBSERVABLE MISMATCH on %r: real has_existing_aggregation=%r "
                "but wrapping-branch observable=%r (an out-of-scope disjunct "
                "must have fired)" % (spec, captured, real_derived))
    if bool(shadow_derived) != real_derived:
        return ("DISAGREEMENT (derived-form decision) on %r\n"
                "  carriers: selected=%r summ=%r filter_summary=%r\n"
                "  shadow (impl region): %r\n"
                "  real patched get_aggregation: %r (error=%r)"
                % (spec, selected, summ, filter_summary, bool(shadow_derived),
                   real_derived, real_error))
    # internal cross-check against the model's own Ensures expression
    spec_value = (any_selected_summary(ToSeq(selected), ToSeq(summ))
                  or filter_summary != 0)
    if bool(shadow_derived) != bool(spec_value):
        return ("INTERNAL: impl region (%r) and the model's Ensures fold (%r) "
                "disagree on selected=%r summ=%r filter_summary=%r"
                % (shadow_derived, spec_value, selected, summ, filter_summary))
    comparisons = 1

    # --- decision 2 (in scope exactly when the derived form was taken) ------
    if real_derived:
        if "mask" not in OBS:
            raise ProbeError("derived form taken but the patched "
                             "annotation_mask was never observed on %r "
                             "(error=%r)" % (spec, real_error))
        real_mask = OBS["mask"]
        universe = list(dict.fromkeys(existing_aliases + added_names
                                      + ["ghost1", "ghost2"]))
        for alias in universe:
            code = CODE[alias]
            shadow_kept = inner_column_kept(code, added, ref_tree)
            real_kept = alias in real_mask
            if bool(shadow_kept) != real_kept:
                return ("DISAGREEMENT (inner-mask decision) on %r, alias=%r\n"
                        "  carriers: alias=%r added=%r ref_tree=%r\n"
                        "  shadow (impl region): kept=%r\n"
                        "  real patched annotation_mask=%r -> kept=%r "
                        "(error=%r)"
                        % (spec, alias, code, added, ref_tree,
                           bool(shadow_kept), sorted(real_mask), real_kept,
                           real_error))
            spec_kept = (seq_contains(ToSeq(added), code)
                         or seq_contains(collect_refs(ToSeq(ref_tree)), code))
            if bool(shadow_kept) != bool(spec_kept):
                return ("INTERNAL: impl region (%r) and the model's Ensures "
                        "fold (%r) disagree on alias=%r added=%r ref_tree=%r"
                        % (shadow_kept, spec_kept, code, added, ref_tree))
            comparisons += 1
    return comparisons


# ---------------------------------------------------------------------------
# input plan
# ---------------------------------------------------------------------------
REF = lambda n: ("ref", n)          # noqa: E731
VAL = ("val",)
COUNT_STAR = ("count",)


def boundary_specs():
    """Boundary + F2P shapes. Every branch of both impl regions is taken."""
    def sp(existing, filt, added):
        return {"existing": existing, "filter": filt, "added": added}

    out = []
    # no pre-existing annotation at all: empty carriers, found stays False
    out.append(sp([], None, [("__count", "sum", COUNT_STAR)]))
    # F2P: alias-only aggregate must NOT force the derived form
    out.append(sp([("exa0", "agg", 0)], None, [("__count", "sum", COUNT_STAR)]))
    # F2P: selected non-aggregate must NOT force the derived form
    out.append(sp([("exa0", "plain", 1)], None,
                  [("__count", "sum", COUNT_STAR)]))
    # F2P: selected aggregate, unreferenced -> derived form, alias pruned
    out.append(sp([("exa0", "agg", 1)], None, [("__count", "sum", COUNT_STAR)]))
    # control: selected aggregate referenced by the summary -> kept
    out.append(sp([("exa0", "agg", 1)], None,
                  [("avg2", "avg", REF("exa0"))]))
    # unselected non-aggregate; unselected window
    out.append(sp([("exa0", "plain", 0)], None,
                  [("__count", "sum", COUNT_STAR)]))
    out.append(sp([("exa0", "window", 0)], None,
                  [("__count", "sum", COUNT_STAR)]))
    # selected window annotation -> contains_over_clause forces derived
    out.append(sp([("exa0", "window", 1)], None,
                  [("__count", "sum", COUNT_STAR)]))
    # filter_summary alone (no selected summary column) forces the derived form
    out.append(sp([], "having", [("__count", "sum", COUNT_STAR)]))
    out.append(sp([], "qualify", [("__count", "sum", COUNT_STAR)]))
    out.append(sp([("exa0", "plain", 1)], "having",
                  [("__count", "sum", COUNT_STAR)]))
    out.append(sp([("exa0", "plain", 1)], "qualify",
                  [("avg2", "avg", REF("exa0"))]))
    # mixed carriers: found set at various positions
    out.append(sp([("exa0", "plain", 1), ("exa1", "agg", 1)], None,
                  [("__count", "sum", COUNT_STAR)]))
    out.append(sp([("exa0", "agg", 1), ("exa1", "plain", 1)], None,
                  [("__count", "sum", COUNT_STAR)]))
    out.append(sp([("exa0", "agg", 0), ("exa1", "plain", 1),
                   ("exa2", "agg", 0)], None,
                  [("__count", "sum", COUNT_STAR)]))
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1),
                   ("exa2", "agg", 1), ("exa3", "agg", 1)], None,
                  [("__count", "sum", COUNT_STAR)]))
    # reference selection: one of several aliases referenced
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1)], None,
                  [("avg2", "avg", REF("exa1"))]))
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1)], None,
                  [("avg2", "avg", ("comp", [REF("exa0"), REF("exa1")]))]))
    # composite trees carrying 0-coded nodes around the refs
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1)], None,
                  [("avg2", "avg", ("comp", [VAL, ("comp", [REF("exa1"), VAL]),
                                             VAL]))]))
    out.append(sp([("exa0", "agg", 1)], None,
                  [("avg2", "avg", ("comp", [VAL, VAL]))]))
    # phantom reference: a Ref to a name the query does not carry
    out.append(sp([("exa0", "agg", 1)], None,
                  [("avg2", "avg", REF("ghost1"))]))
    out.append(sp([("exa0", "agg", 1)], None,
                  [("avg2", "avg", ("comp", [REF("ghost1"),
                                             REF("exa0")]))]))
    # reference to an UNSELECTED alias, with a selected aggregate forcing the
    # derived form (so decision 2 is in scope)
    out.append(sp([("exa0", "agg", 0), ("exa1", "agg", 1)], None,
                  [("avg2", "avg", REF("exa0"))]))
    # two pushed-out summary names: the mask is the union over both
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1)], None,
                  [("__count", "sum", REF("exa0")),
                   ("avg2", "avg", REF("exa1"))]))
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1)], None,
                  [("__count", "sum", COUNT_STAR),
                   ("avg2", "avg", REF("exa1"))]))
    # deep / wide reference trees
    deep = REF("exa0")
    for _ in range(4):
        deep = ("comp", [deep])
    out.append(sp([("exa0", "agg", 1)], None, [("avg2", "avg", deep)]))
    wide = ("comp", [REF("exa0"), REF("exa1"), REF("ghost2"), VAL,
                     ("comp", [REF("exa2"), VAL])])
    out.append(sp([("exa0", "agg", 1), ("exa1", "agg", 1),
                   ("exa2", "agg", 1), ("exa3", "agg", 1)], None,
                  [("avg2", "avg", wide)]))
    # the same shapes with a HAVING filter also present
    out.append(sp([("exa0", "agg", 1), ("exa1", "plain", 1)], "having",
                  [("avg2", "avg", REF("exa0"))]))
    out.append(sp([("exa0", "plain", 0)], "having",
                  [("__count", "sum", COUNT_STAR)]))
    # unselected aggregate + HAVING (the axis-1/axis-2 crossing)
    out.append(sp([("exa0", "agg", 0)], "qualify",
                  [("avg2", "avg", REF("exa0"))]))
    # every single-annotation combination of (selected, kind)
    for kind in ("agg", "plain", "window"):
        for sel in (0, 1):
            out.append(sp([("exa0", kind, sel)], None,
                          [("__count", "sum", COUNT_STAR)]))
            out.append(sp([("exa0", kind, sel)], None,
                          [("avg2", "avg", REF("exa0"))]))
    return out


def rand_tree(rng, depth):
    r = rng.random()
    if depth <= 0 or r < 0.45:
        if r < 0.35:
            return REF(rng.choice(NAME_POOL))
        return VAL
    k = rng.randint(1, 3)
    return ("comp", [rand_tree(rng, depth - 1) for _ in range(k)])


def random_spec(rng):
    n = rng.randint(0, 4)
    aliases = EXISTING_NAMES[:n]
    existing = [(a, rng.choice(("agg", "plain", "window")),
                 1 if rng.random() < 0.65 else 0) for a in aliases]
    filt = rng.choice((None, None, None, "having", "qualify"))
    n_added = 1 if rng.random() < 0.8 else 2
    added = []
    for alias in ADDED_NAMES[:n_added]:
        if rng.random() < 0.25:
            added.append((alias, "sum", COUNT_STAR))
        else:
            added.append((alias, rng.choice(("sum", "avg")),
                          rand_tree(rng, rng.randint(0, 3))))
    return {"existing": existing, "filter": filt, "added": added}


def main():
    _setup_django()
    _install_spies()
    from django.db import connection, models
    from django.db.models import Avg, Count, Q, Sum, Value, Window
    from django.db.models.expressions import (ExpressionWrapper, Func, Ref)
    from django.db.models.fields import IntegerField
    from django.db.models.functions import Lower, RowNumber
    from django.db.models.sql.query import Query

    if not hasattr(Ref, "get_refs"):
        print("status=error real Ref.get_refs absent (gold patch not applied?)")
        return 1

    class ConfThing(models.Model):
        num = models.IntegerField()
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(ConfThing)

    ctx = (Query, Count, Lower, Sum, Avg, Window, RowNumber, Q, Ref, Value,
           Func, ExpressionWrapper, IntegerField, ConfThing)

    probes = 0
    comparisons = 0
    derived_true = 0
    derived_false = 0
    mask_probes = 0

    def one(spec):
        nonlocal probes, comparisons, derived_true, derived_false, mask_probes
        try:
            res = run_probe(spec, ctx)
        except ProbeError as exc:
            print("status=error probe could not be driven: %s" % (exc,))
            return False
        if isinstance(res, str):
            print(res)
            print("status=fail shadow disagrees with the real patched "
                  "get_aggregation (seed=%d)" % SEED)
            return False
        probes += 1
        comparisons += res
        if res > 1:
            mask_probes += 1
            derived_true += 1
        else:
            derived_false += 1
        return True

    boundary = boundary_specs()
    for spec in boundary:
        if not one(spec):
            return 1

    rng = random.Random(SEED)
    while probes < N_PROBES:
        if not one(random_spec(rng)):
            return 1

    if derived_true == 0 or derived_false == 0 or mask_probes == 0:
        print("status=error input plan degenerate: derived_true=%d "
              "derived_false=%d mask_probes=%d" % (derived_true, derived_false,
                                                   mask_probes))
        return 1

    print("G-CONF OK: contract-stripped impl regions of "
          "existing_summary_forces_derived / inner_column_kept agree with the "
          "REAL patched Query.get_aggregation on %d probes (%d boundary + fuzz, "
          "seed %d): %d took the derived form, %d did not, %d inner-mask "
          "comparisons; 0 disagreements."
          % (probes, len(boundary), SEED, derived_true, derived_false,
             comparisons - probes))
    print(json.dumps({
        "status": "pass",
        "probes": probes,
        "comparisons": comparisons,
        "boundary": len(boundary),
        "derived_form_taken": derived_true,
        "derived_form_not_taken": derived_false,
        "inner_mask_probes": mask_probes,
        "disagreements": 0,
        "seed": SEED,
        "oracle": "called: real patched Query.get_aggregation "
                  "(django/db/models/sql/query.py) + real get_refs",
        "shadow": "direct (contract-stripped impl region of model.py)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
