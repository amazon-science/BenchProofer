#!/usr/bin/env python3
"""G-CONF for django__django-10554.

Differential conformance test of the R/I legs of
`implementation_resolveOrderColumn` (Solution.lean) against the behaviour of the
gold `patch.diff`, run inside the instance container with that patch applied.

WHAT IS MODELED
---------------
The patched region is the combinator branch of `SQLCompiler.get_order_by`
(`django/db/models/sql/compiler.py`) together with the new column-adding helper
on `Query` (`django/db/models/sql/query.py`). For one ORDER BY term:

    for idx, (sel_expr, _, col_alias) in enumerate(self.select):
        if is_ref and col_alias == src.refs:
            src = src.source
        elif col_alias:
            continue
        if src == sel_expr:
            resolved -> position idx+1; break
    else:                                  # no column matched
        if col_alias:                      # trailing column's alias (loop var)
            raise DatabaseError(...)
        self.query.add_select_col(src)     # select += col, ; values_select += name,
        resolved -> position len(self.query.select)

THE ORACLE IS THE REAL CODE, NOT A TRANSLITERATION OF IT
--------------------------------------------------------
The previous revision of this file hand-transliterated that suite into Python and
compared the transliteration with the shadow. Three of the facts the spec now
turns on are invisible to any such transliteration, because they are properties of
the real objects and of CPython's own scoping rather than of the control flow:

  * `elif col_alias:` / `if col_alias:` test the alias FOR TRUTH, so a present but
    empty name is no alias;
  * `add_select_col` performs TWO appends, `self.select += col,` and then
    `self.values_select += col.output_field.name,`, and asking a real expression
    for that name can RAISE (`FieldError`) after the first append has landed —
    the column is in the selected columns and the label list is behind;
  * `col_alias` is the loop variable of the scan, so the value the no-match suite
    tests is the alias of the LAST COLUMN THE SCAN VISITED — and where the scanned
    list was empty the name is not bound at all, so reading it raises
    `UnboundLocalError` and the suite adds nothing.
  * likewise `src.refs` is only readable while `src` is still the reference: once
    the scan has substituted `src = src.source`, a further iteration reading
    `src.refs` raises `AttributeError`.

So the oracle here EXTRACTS the patched suite from the installed
`compiler.py` source at run time (`inspect.getsource`, sliced at the `for` header
and its `else:`), compiles it in a copy of that module's own globals, and runs it
over REAL Django expression objects and a REAL `Query` instance whose
`add_select_col` is the real patched helper. Nothing about the branch structure,
the truth tests, the two appends or the loop-variable scoping is restated here;
if the installed code differs from the sketch above, the extraction assertions
below fail loudly rather than the check passing against a model of itself.

The expressions are drawn from a fixed pool of real ones covering the three value
labels a column can contribute -- a bound model field's `Col` (a name), `Random()`
and `RawSQL` (an output field with no name), `Value(1)` (no output field at all,
so no label can be produced) -- plus real `Ref(refs, source)` wrappers for the
reference case.

WHAT THE MODEL ID IS. Real `==` on expressions is `self.identity == other.identity`,
and `identity` collapses a `fields.Field` constructor argument to its CLASS. So it
DOES NOT read the field instance, and it does not determine the value label the
expression contributes: two `Col`s over different fields of the same class under
the same alias are the SAME EXPRESSION to `==` while their `output_field.name`
differ. The bridge therefore maps each pool object to the index of its class under
the real `==` -- the QUOTIENT of the pool by the callee's own equality -- and its
label separately, and asserts the quotient is EXACT IN BOTH DIRECTIONS: for every
ordered pair, `a == b` iff their model ids agree. That is what makes the Lean
carrier faithful, where a pool asserted pairwise UNEQUAL would only have excluded
the collapse by construction. The pool deliberately CONTAINS such a collapsed
class (three `Col`s under one alias over three different `CharField`s, and two
`Random()`s), and the run FAILS unless the fuzz both drew a match decided inside
one and would have disagreed with a shadow that compared the label too (the
`structural` control below).

TWO DISTINCT LISTS. The real code SCANS `self.select`, the COMPILER's list
(`get_select()`: extra_select ++ (query.select | default_cols) ++
annotation_select, each entry a `(sel_expr, sql, col_alias)` triple) -- both the
leaked `col_alias` and the matched position `idx+1` come from there -- while it
APPENDS to `self.query.select` and reports `len(self.query.select)`. That is the
QUERY's own list, neither the scanned one nor a prefix of it. `values_select` is
load-bearing rather than decorative: `get_combinator_sql` pushes the outer query's
`values_select` down into every arm of the combination, so a column added to
`select` but not named in `values_select` leaves each arm selecting one fewer
column than the outer query and the emitted position points past the end of every
arm's list. The three lists are therefore fuzzed independently and both mutated
ones are compared.

`shadow(...)` is the R/I transliteration of `implementation_resolveOrderColumn`
over the bridged view (expression -> (model id, label class), alias -> optional
string). The two must agree on every fuzzed input: on the reported position, on
BOTH mutated lists -- compared as FULL VIEWS, id and label, not ids alone -- and on
WHICH of the six outcome classes came out. Every one of those classes must be
reached or the run fails. The usability property the spec's second conjunct asserts
is additionally checked OF THE ORACLE, i.e. of the real code, on every input that
arrives in correspondence.

DOMAIN NOTES. The fuzz includes inputs the real compiler cannot assemble but on
which the extracted code is still well defined (an empty alias name; a reference
whose `refs` is absent or empty; a query whose two column-state parts are out of
correspondence on arrival) -- the claim tested there is that the model agrees with
what the CODE does, and the usability conjunct is checked only under the
correspondence hypothesis the spec itself states. Conversely the model admits one
shape this fuzz does not produce: a `QExpr` whose id no pool object carries, since
every fuzzed expression is a pool object. Exit 0 iff zero disagreements, zero
usability breaks, every outcome class reached, a match decided inside a collapsed
class drawn, and the `structural` control disagreeing, over >=1e5 cases.
Django + stdlib only.
"""
import inspect
import random
import sys
import textwrap

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )
django.setup()

from django.contrib.auth.models import User                    # noqa: E402
from django.contrib.contenttypes.models import ContentType     # noqa: E402
from django.core.exceptions import FieldError                  # noqa: E402
from django.db import DatabaseError                            # noqa: E402
from django.db.models.expressions import (                     # noqa: E402
    Col, RawSQL, Random, Ref, Value,
)
from django.db.models.sql import compiler as compiler_mod      # noqa: E402
from django.db.models.sql.query import Query                   # noqa: E402

SEED = 10554
N_CASES = 200_000

# --------------------------------------------------------------------------
# 1. The oracle: the patched suite itself, lifted out of the installed source.
# --------------------------------------------------------------------------
FOR_HEADER = "for idx, (sel_expr, _, col_alias) in enumerate(self.select):"


def _indent(line):
    return len(line) - len(line.lstrip())


def _extract_patched_suite():
    """Slice the combinator scan + its `else:` suite out of the real
    `get_order_by`, and wrap it in a function of (self, src, is_ref, resolved).

    Every assertion here is a guard against the check passing while shadowing
    something other than the patched code."""
    lines = inspect.getsource(compiler_mod.SQLCompiler.get_order_by).splitlines()
    heads = [i for i, l in enumerate(lines) if l.strip() == FOR_HEADER]
    if len(heads) != 1:
        raise AssertionError("expected exactly one combinator scan, got %d" % len(heads))
    i0 = heads[0]
    base = _indent(lines[i0])
    j = i0 + 1
    while j < len(lines) and (not lines[j].strip() or _indent(lines[j]) > base):
        j += 1
    if j >= len(lines) or lines[j].strip() != "else:":
        raise AssertionError("scan is not followed by a for/else suite: %r"
                             % (lines[j] if j < len(lines) else None))
    j += 1
    while j < len(lines) and (not lines[j].strip() or _indent(lines[j]) > base):
        j += 1
    block = "\n".join(lines[i0:j])
    tail = lines[j].strip() if j < len(lines) else ""
    if not tail.startswith("sql, params = self.compile(resolved)"):
        raise AssertionError("unexpected statement after the suite: %r" % tail)
    for needle in ("if is_ref and col_alias == src.refs:", "src = src.source",
                   "elif col_alias:", "continue", "if src == sel_expr:", "break",
                   "if col_alias:", "raise DatabaseError(",
                   "self.query.add_select_col(src)",
                   "len(self.query.select)", "RawSQL("):
            if needle not in block:
                raise AssertionError("suite does not contain %r" % needle)
    helper = inspect.getsource(Query.add_select_col)
    for needle in ("self.select += col,", "self.values_select += col.output_field.name,"):
        if needle not in helper:
            raise AssertionError("add_select_col helper is not the patched one: %r" % helper)
    fn_src = ("def _patched_suite(self, src, is_ref, resolved):\n"
              + textwrap.indent(textwrap.dedent(block), "    ") + "\n")
    g = dict(vars(compiler_mod))          # the real module's own globals
    exec(compile(fn_src, "<patched-suite>", "exec"), g)
    return g["_patched_suite"], block, helper


PATCHED_SUITE, SUITE_SRC, HELPER_SRC = _extract_patched_suite()


class _Compiler:
    """The only two attributes the suite reads off `self`."""

    def __init__(self, select, query):
        self.select = select
        self.query = query


class _Resolved:
    """Records what the suite renders the ORDER BY term to. Observation
    scaffolding: the RawSQL it is handed is built by the real code."""

    def __init__(self):
        self.calls = []

    def set_source_expressions(self, exprs):
        self.calls.append(exprs)


# --------------------------------------------------------------------------
# 2. The bridge: real expression <-> (pool id, value-label class).
# --------------------------------------------------------------------------
NAME, ANON, UNDET = "name", "anon", "undet"


def label_class(expr):
    """The value label this expression contributes when it becomes one of the
    query's selected columns, as the real `add_select_col` would read it."""
    try:
        field = expr.output_field
    except FieldError:
        return (UNDET, None)
    return (NAME, field.name) if field.name is not None else (ANON, None)


def _build_pool():
    app_label = ContentType._meta.get_field("app_label")
    username = User._meta.get_field("username")
    model_name = ContentType._meta.get_field("model")
    plain = [
        Col("t0", app_label),      # name 'app_label'
        Col("t1", app_label),      # a DIFFERENT expression with the SAME label
        Col("t2", username),       # name 'username'
        # The converse case, and the one a pool asserted pairwise unequal cannot
        # hold: THE SAME EXPRESSION under the real `==` (same alias, same field
        # CLASS, and `identity` reads no more than that) contributing a DIFFERENT
        # value label. Three of them, so a collapsed class is not just a pair.
        Col("t0", username),       # == Col("t0", app_label); name 'username'
        Col("t0", model_name),     # == both of those;        name 'model'
        Random(),                  # output field with no name
        Random(),                  # == the other Random(), a distinct object
        RawSQL("1", ()),           # ditto, different identity
        Value(1),                  # no output field: no label can be produced
        Value(2),
    ]
    refs_names = [None, "", "a", "b", "c"]
    # Reference wrappers to depth THREE. A `Ref`'s source may itself be a `Ref`
    # -- `resolve_ref` hands back whatever the named entry holds -- so a
    # reference ORDER BY term is a CHAIN of named wrappers, not one wrapper over
    # a plain expression. A pool of depth-1 wrappers only cannot produce a term
    # the scan realiases twice, which is the whole re-substitution leg. Deeper
    # levels wrap EXISTING pool objects so that a term's inner wrapper is the
    # same object a scanned result column may hold, which is what lets a
    # realiased term meet the very wrapper below it.
    d1 = [Ref(r, s) for r in refs_names for s in plain]
    d2 = [Ref(r, s) for r in refs_names for s in d1[:14]]
    d3 = [Ref(r, s) for r in ("a", "b") for s in d2[:8]]
    wrapped = d1 + d2 + d3
    objs = plain + wrapped
    seen = set()
    for cls in (label_class(e) for e in plain):
        seen.add(cls[0])
    for want in (NAME, ANON, UNDET):
        if want not in seen:
            raise AssertionError("pool has no %s-label expression: %r" % (want, seen))
    return plain, wrapped, d1, d2, d3


def _quotient(objs):
    """Model id of each pool object: the index of its class under the REAL `==`.

    The Lean carrier's `QExpr.id` is what `QExpr.sameExpr` compares, and the real
    comparison the scan makes is `src == sel_expr`, i.e. `identity` equality. So
    the bridge must send two objects to the same id EXACTLY when the callee calls
    them the same expression -- which it does for two `Col`s that differ only in
    which field of one class they name. Asserted exact in BOTH directions over
    every ordered pair; a one-directional check (all distinct) would be satisfied
    by a pool built to avoid the collapse."""
    mid = {}
    reps = []
    for o in objs:
        for i, r in enumerate(reps):
            if o == r:
                mid[id(o)] = i
                break
        else:
            mid[id(o)] = len(reps)
            reps.append(o)
    for a in objs:
        if not (a == a):
            raise AssertionError("pool entry %r is not equal to itself" % (a,))
        for b in objs:
            if (a == b) != (mid[id(a)] == mid[id(b)]):
                raise AssertionError(
                    "model id is not the quotient by the real `==`: %r %r "
                    "(== %r, ids %d %d)" % (a, b, a == b, mid[id(a)], mid[id(b)]))
    return mid, len(reps)


PLAIN, WRAPPED, D1, D2, D3 = _build_pool()
ALL_OBJS = PLAIN + WRAPPED
MID, N_CLASSES = _quotient(ALL_OBJS)                      # model id of an object
LABEL = {id(o): label_class(o) for o in ALL_OBJS}
VIEW = {id(o): (MID[id(o)], LABEL[id(o)]) for o in ALL_OBJS}

# The two facts about the carrier the bridge now has to be able to express, each
# asserted PRESENT in the pool rather than avoided by it: expressions the callee
# calls the same that contribute DIFFERENT labels, and expressions it calls
# different that contribute the SAME label. Without the first the run cannot
# reach the leg where `==` collapses; without the second `sameExpr` would be
# indistinguishable from label equality.
_SAME_EXPR_DIFF_LABEL = [(a, b) for a in ALL_OBJS for b in ALL_OBJS
                         if a is not b and MID[id(a)] == MID[id(b)]
                         and LABEL[id(a)] != LABEL[id(b)]]
_DIFF_EXPR_SAME_LABEL = [(a, b) for a in ALL_OBJS for b in ALL_OBJS
                         if MID[id(a)] != MID[id(b)]
                         and LABEL[id(a)] == LABEL[id(b)]]
if not _SAME_EXPR_DIFF_LABEL:
    raise AssertionError("pool holds no same-expression/different-label pair: "
                         "the collapse `==` performs is not in the domain")
if not _DIFF_EXPR_SAME_LABEL:
    raise AssertionError("pool holds no different-expression/same-label pair")


def mids(objs):
    return [MID[id(o)] for o in objs]


def views(objs):
    """The bridged view of a list of real expressions: id AND label for each, so
    a mutated column list is compared on both components rather than on ids
    alone."""
    return [VIEW[id(o)] for o in objs]


def as_order_src(obj):
    """The type bridge for the ORDER BY term: a real expression -> the model's
    `OrderSrc` = (a stack of reference wrappers, outermost first, over the
    expression no wrapper stands over).

    Peeling is by the SAME test the callee's own realiasing loop makes -- does
    this object hold a `source` under a name -- so a term wrapped n times bridges
    to n links, whatever n is."""
    links = []
    while isinstance(obj, Ref):
        links.append((MID[id(obj)], obj.refs))
        obj = obj.source
    return links, VIEW[id(obj)]


def src_compared(links, base):
    """`OrderSrc.compared`: the term as `==` sees it, carrying the value label it
    would contribute. A wrapper is its own identity for comparison, but its
    output field is its source's -- `Ref.output_field` delegates -- so the label
    is the BASE's, measured: `Ref(Col)` reports that column's field name."""
    return (links[0][0], base[1]) if links else base


def src_refs(links):
    """`OrderSrc.refs?`: the name the term currently stands under, or nothing at
    all once no wrapper is left -- which is the only state in which reading the
    name is not possible."""
    return None if not links else ("some", links[0][1])


# --------------------------------------------------------------------------
# 3. The oracle call.
# --------------------------------------------------------------------------
def oracle(select, query_select, values_select, is_ref, src):
    """Run the extracted patched suite and classify what it did.

    Returns ("resolved", pos, new_query_views, new_values), ("noMatch",) or
    ("aborted", new_query_views, new_values, why). `select` is the scanned
    compiler list of (expr, sql, alias) triples; the query's own two lists live
    on a real Query whose add_select_col is the real helper. The selected-column
    list comes back as bridged VIEWS (id and label), so a wrong column appended
    inside one `==` class is still visible."""
    q = Query.__new__(Query)
    q.select = tuple(query_select)
    q.values_select = tuple(values_select)
    comp = _Compiler(list(select), q)
    rec = _Resolved()
    try:
        PATCHED_SUITE(comp, src, is_ref, rec)
    except DatabaseError:
        return ("noMatch",)
    except UnboundLocalError as exc:
        if "col_alias" not in str(exc):
            raise
        return ("aborted", views(q.select), list(q.values_select), "no-column-visited")
    except AttributeError as exc:
        if "refs" not in str(exc):
            raise
        return ("aborted", views(q.select), list(q.values_select), "refs-after-switch")
    except FieldError as exc:
        if "output_field" not in str(exc):
            raise
        return ("aborted", views(q.select), list(q.values_select), "no-label")
    if comp.select != list(select):
        raise AssertionError("the suite mutated the SCANNED list")
    if len(rec.calls) != 1 or len(rec.calls[0]) != 1:
        raise AssertionError("unexpected rendering: %r" % (rec.calls,))
    return ("resolved", int(rec.calls[0][0].sql), views(q.select),
            list(q.values_select))


# --------------------------------------------------------------------------
# 4. The shadow: implementation_resolveOrderColumn, over the bridged view.
# --------------------------------------------------------------------------
def has_alias(alias):
    """`hasAlias`: an optional alias counts only where it tests true."""
    return alias is not None and alias != ""


def added_outcome(cur, query_select, values_select):
    """`addedOutcome`: the column joins the selected columns, and then its label
    joins the label list -- if it has one to contribute."""
    new_query = list(query_select) + [cur]
    kind, name = cur[1]
    if kind == UNDET:
        return ("aborted", new_query, list(values_select), "no-label")
    return ("resolved", len(new_query), new_query,
            list(values_select) + [name if kind == NAME else None])


def same_expr(a, b):
    """`QExpr.sameExpr`: two expressions are the same expression exactly when
    their identities agree. Real `==` is `self.identity == other.identity` and
    `identity` maps a field argument to its CLASS, so it does not read the field
    instance and does not settle the label -- the label component takes no part
    in this test."""
    return a[0] == b[0]


def shadow(result_cols, query_select, values_select, is_ref, links, base,
           match=same_expr):
    """R/I transliteration of implementation_resolveOrderColumn (Solution.lean).
    `result_cols` are ((mid, label), alias) pairs; `query_select` are views;
    `links`/`base` are the bridged wrapper stack and its base expression.

    `match` is the comparison the scan makes, defaulted to the modeled
    `QExpr.sameExpr`. The `structural` control below passes full-view equality
    instead -- a shadow that also demands the labels agree -- and the run REQUIRES
    that control to disagree with the real code somewhere, which is what makes the
    id-only test a measured fact rather than a stipulation."""
    links = list(links)
    idx = 0
    for (expr, col_alias) in result_cols:
        if is_ref and src_refs(links) is None:
            return ("aborted", list(query_select), list(values_select),
                    "refs-after-switch")
        alias_match = is_ref and src_refs(links) == ("some", col_alias)
        if alias_match:
            links = links[1:]
        if (alias_match or not has_alias(col_alias)) and match(
                src_compared(links, base), expr):
            return ("resolved", idx + 1, list(query_select), list(values_select))
        idx += 1
    if not result_cols:                       # getLast? = none
        return ("aborted", list(query_select), list(values_select),
                "no-column-visited")
    if has_alias(result_cols[-1][1]):
        return ("noMatch",)
    return added_outcome(src_compared(links, base), query_select, values_select)


# --------------------------------------------------------------------------
# 5. The usability property, checked of the ORACLE.
# --------------------------------------------------------------------------
def usability_break(o, n_result_cols, query_select, values_select):
    """`outcomeUsable`, read off the real code's own result: a reported position
    is a genuine 1-based ordinal OF THE RIGHT LIST -- of the scanned result
    columns when the query state came back untouched, and of the query's own
    selected columns (its new trailing one) when it grew by exactly one -- the
    two parts stay in correspondence, and where no position is reported the
    labels are exactly as they arrived and at most one column was added."""
    if o[0] == "resolved":
        _, pos, oq, ov = o
        if len(ov) != len(oq) or pos < 1:
            return True
        if len(oq) == len(query_select):
            return (oq != list(query_select) or ov != list(values_select)
                    or pos > n_result_cols)
        return len(oq) != len(query_select) + 1 or pos != len(oq)
    if o[0] == "aborted":
        _, oq, ov, _why = o
        return ov != list(values_select) or len(oq) > len(query_select) + 1
    return False


# --------------------------------------------------------------------------
# 6. Fuzz.
# --------------------------------------------------------------------------
CLASSES = ("resolved-match", "resolved-added", "noMatch",
           "aborted:no-column-visited", "aborted:refs-after-switch",
           "aborted:no-label")


def outcome_class(o, query_select):
    if o[0] == "noMatch":
        return "noMatch"
    if o[0] == "aborted":
        return "aborted:" + o[3]
    return ("resolved-match" if len(o[2]) == len(query_select)
            else "resolved-added")


def main():
    rng = random.Random(SEED)
    aliases = [None, "", "a", "b", "c"]
    labels = ["app_label", "username", "model", None]
    mismatches = 0
    usability_breaks = 0
    checked = 0
    seen = {c: 0 for c in CLASSES}
    depth_seen = {0: 0, 1: 0, 2: 0, 3: 0}
    # Draws whose MATCH was decided inside one `==` class while the two
    # expressions contribute DIFFERENT value labels: the leg on which a shadow
    # comparing the label too would report the added-column outcome where the
    # real code reports a position. Required non-zero.
    collapsed_matches = 0
    # Disagreements of the `structural` control -- the same shadow with full-view
    # equality in place of `sameExpr` -- with the real code. Required non-zero:
    # if this is 0 the fuzz never distinguished the two comparisons and the
    # agreement above would say nothing about which one the callee makes.
    structural_mismatches = 0
    for _ in range(N_CASES):
        # The scanned list: 0..5 columns. Empty is in domain -- the suite is
        # defined there (it reads an unbound loop variable and stops).
        n = rng.randint(0, 5)
        select = []
        # A scanned column may hold ANY pool member, wrappers included, so a
        # realiased term can meet the very wrapper below it -- the shape on which
        # a second realiasing happens.
        col_pool = PLAIN + D1 + D2
        for _i in range(n):
            select.append((rng.choice(col_pool), "sql", rng.choice(aliases)))
        # The QUERY's own two lists, independent of the scanned one: shorter,
        # longer, empty (default_cols) or unrelated in content. In
        # correspondence most of the time, which is the real invariant and the
        # hypothesis the usability conjunct is stated under.
        m = rng.randint(0, 5)
        query_select = [rng.choice(PLAIN) for _i in range(m)]
        k = m if rng.random() < 0.85 else rng.randint(0, 5)
        values_select = [rng.choice(labels) for _i in range(k)]
        is_ref = rng.random() < 0.5
        # A reference term is a real `Ref`, as it is in the callee -- at any
        # wrapping depth the pool holds.
        src = rng.choice(WRAPPED) if is_ref else rng.choice(ALL_OBJS)
        links, base = as_order_src(src)
        depth_seen[min(len(links), 3)] += 1

        o = oracle(select, query_select, values_select, is_ref, src)
        cols_view = [(VIEW[id(e)], a) for e, _sql, a in select]
        s = shadow(cols_view, views(query_select), values_select, is_ref,
                   links, base)
        if o != s:
            mismatches += 1
            if mismatches <= 5:
                print("MISMATCH select=%r query_select=%r values=%r is_ref=%r "
                      "src=%r" % ([(MID[id(e)], a) for e, _q, a in select],
                                  mids(query_select), values_select, is_ref,
                                  MID[id(src)]))
                print("  oracle:", o)
                print("  shadow:", s)
        # The control: the same shadow demanding the LABELS agree as well.
        ctrl = shadow(cols_view, views(query_select), values_select, is_ref,
                      links, base, match=lambda a, b: a == b)
        if o != ctrl:
            structural_mismatches += 1
        seen[outcome_class(o, query_select)] += 1
        # Did the real code resolve AT a column whose expression it calls the
        # same as the term's while the two contribute different labels? The
        # carried expression's label is the term's base's in every case.
        if o[0] == "resolved" and len(o[2]) == len(query_select):
            matched = select[o[1] - 1][0]
            if LABEL[id(matched)] != base[1]:
                collapsed_matches += 1
        if len(values_select) == len(query_select) and usability_break(
                o, len(select), views(query_select), values_select):
            usability_breaks += 1
            if usability_breaks <= 5:
                print("USABILITY-BREAK select=%r query_select=%r values=%r "
                      "is_ref=%r src=%r"
                      % ([(MID[id(e)], a) for e, _q, a in select],
                         mids(query_select), values_select, is_ref, MID[id(src)]))
                print("  oracle:", o)
        checked += 1

    cover = " ".join("%s=%d" % (c, seen[c]) for c in CLASSES)
    print("provenance: django %s, suite %d lines, helper %d lines"
          % (".".join(str(v) for v in django.VERSION[:3]),
             len(SUITE_SRC.splitlines()), len(HELPER_SRC.splitlines())))
    print("pool: plain=%d d1=%d d2=%d d3=%d total=%d objects, %d `==` classes"
          % (len(PLAIN), len(D1), len(D2), len(D3), len(ALL_OBJS), N_CLASSES))
    print("collapse: %d same-expression/different-label pairs, "
          "%d different-expression/same-label pairs"
          % (len(_SAME_EXPR_DIFF_LABEL), len(_DIFF_EXPR_SAME_LABEL)))
    print("term wrapping depth:", depth_seen)
    print("coverage:", cover)
    print("collapsed matches: %d; structural-control disagreements: %d"
          % (collapsed_matches, structural_mismatches))
    # A run that never fuzzed a term wrapped more than once says nothing about
    # the re-substitution leg, so require the deeper chains to have been drawn.
    if depth_seen[2] == 0 or depth_seen[3] == 0:
        print("status=fail checked=%d no multiply-wrapped term drawn (%r)"
              % (checked, depth_seen))
        sys.exit(1)
    # Every outcome class the spec distinguishes must have been reached: a run
    # that never took the added-column path, or never reached one of the three
    # stops, proves nothing about the legs it skipped.
    missing = [c for c in CLASSES if seen[c] == 0]
    if missing:
        print("status=fail checked=%d unreached=%s (%s)"
              % (checked, ",".join(missing), cover))
        sys.exit(1)
    # The leg the whole bridge turns on. `==` collapses two expressions that
    # contribute different labels, so the scan can resolve AT such a column; a
    # run that never drew one has not tested the comparison the model makes, and
    # a control that agrees everywhere means id-only and full-view equality were
    # never told apart on this fuzz. Both are hard requirements: without them the
    # agreement measured above is vacuous on exactly the leg the reviewer of a
    # pairwise-unequal pool could not see.
    if collapsed_matches == 0 or structural_mismatches == 0:
        print("status=fail checked=%d collapsed_matches=%d "
              "structural_control_disagreements=%d (the collapse `==` performs "
              "was not exercised)"
              % (checked, collapsed_matches, structural_mismatches))
        sys.exit(1)
    if mismatches == 0 and usability_breaks == 0:
        print("status=pass checked=%d mismatches=0 usability_breaks=0 (%s)"
              % (checked, cover))
        sys.exit(0)
    print("status=fail checked=%d mismatches=%d usability_breaks=%d (%s)"
          % (checked, mismatches, usability_breaks, cover))
    sys.exit(1)


if __name__ == "__main__":
    main()
