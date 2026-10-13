#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15375 (nagini).

SHADOW
------
The impl region of ``model.py``'s ``resolve_aggregation``, copied VERBATIM
below with only the contract calls stripped (the model IS Python, so there is
no transliteration step). What was removed, and nothing else:

  * ``Requires(...)``/``Ensures(...)`` in ``Expression.__init__`` and
    ``FallbackValue.__init__`` (the ``Acc``/equality frame); the field
    assignments are kept exactly as written.
  * the ``Assert(not wrapper.is_final_aggregation)`` line inside the impl
    region (a Nagini proof obligation, not computation).
  * the ``# pre-conditions-*`` / ``# post-conditions-*`` marker comments.

The control flow, the variable names (``c``, ``supplied``, ``resolved``,
``wrapper``), and the two-step ``Expression(False, True)`` then
``wrapper.is_final_aggregation = c.is_final_aggregation`` sequence are preserved
as-is. No restructuring: a shadow that collapsed those two steps into
``Expression(requested_final, True)`` would be a paraphrase and would silently
stop testing the fact that the real wrapper is born UNMARKED and only becomes
marked by the gold assignment -- which is the behaviour under specification.

There are no ``@Pure`` helpers and no ``@ContractOnly`` callees to bridge
(``model.py``'s axioms-start/pure-start regions are both empty, and
mapping.md §3 records that this bundle consumes no axiomatized callee), so the
shadow needs no PSeq shim and no stand-in bodies.

ORACLE  --  CALLED, NOT TRANSLITERATED
--------------------------------------
The REAL patched repo function named by mapping.md §1:
``Aggregate.resolve_expression(self, query, allow_joins, reuse, summarize,
for_save)`` at ``django/db/models/aggregates.py:50`` (fallback-wrapping tail,
body lines 63-70 post-patch). The gate applies ``patch.diff`` to /testbed and
sets ``PYTHONPATH=/testbed`` before this script runs, so ``import django``
resolves the patched module; ``_setup_django()`` configures an in-memory
sqlite backend and a minimal model under the already-registered
``contenttypes`` app label (no fabricated ``INSTALLED_APPS`` entry), which is
all ``resolve_expression`` needs to resolve field references.

This is a genuine call into the repository: each probe constructs a real
``Sum``/``Avg``/``Min``/``Max``/``StdDev``/``Variance``/``Count`` over a real
model field (or over an operand that itself contains an aggregate, or over a
mixed-type combination) and invokes ``agg.resolve_expression(query, True, None,
summarize)``, then observes the returned expression -- including its SOURCE
EXPRESSIONS. Nothing about the patched tail is reimplemented here; in
particular the check does NOT hardcode "a default yields a marked Coalesce",
nor which inputs raise: it asks the real object and compares.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
Generation runs CONCRETE -> ABSTRACT, and every abstract input is computed from
the WRITTEN construction alone -- never from the oracle's answer -- so the
bridge cannot echo the oracle:

  concrete realization                        ->  model input
    ``summarize`` argument                    ->  ``requested_final``
    ``default is None``                       ->  ``fallback is None``
    the ``default`` OBJECT itself             ->  ``fallback`` (a FallbackValue
                                                  standing for that object)
    ``hasattr(default,'resolve_expression')`` ->  ``fallback_is_expression``
    the written default can stand as a
      fallback source without resolution:
      ``hasattr(_as_coalesce_arg(default),
      'as_sql')`` -- the written object as
      the fallback-supplying expression
      itself represents it (an expression is
      taken as is; a str becomes ``F(str)``,
      which has no as_sql; any other plain
      value becomes ``Value(v)``, which has)
      -- see Func._parse_expressions,
      expressions.py:184-189                  ->  ``fallback.usable``
    the operand itself contains an aggregate  ->  ``aggregating_operand``
    the aggregation carries a restricting
      condition that was LEFT AS WRITTEN and
      whose written form has NO ``as_sql``.
      "Left as written" is falsiness: a
      present ``Q`` with no children, which
      ``Node.__bool__`` makes FALSY
      (django/utils/tree.py:60-62), so the
      ``and`` at aggregates.py:53 short-
      circuits and the condition is never
      replaced by a resolved one. The second
      half is required because falsiness does
      not imply uncompilability: a childless
      ``WhereNode`` is FALSY too, so ``:53``
      short-circuits on it as well, yet
      ``WhereNode`` defines ``as_sql``
      (django/db/models/sql/where.py:65) and
      the aggregation it restricts stays
      usable as it stands. Computed from the
      WRITTEN condition alone -- ``filt is
      not None and not bool(filt) and not
      hasattr(filt,'as_sql')`` -- and
      cross-checked against the value the
      realization space declares, so the
      declared column cannot drift from the
      written object                          ->  ``vacuous_condition``
    what putting the OPERAND through
      resolution came back with: whether
      that resolved form has an ``as_sql``.
      Obtained by calling THAT step --
      ``written_operand.resolve_expression``,
      which ``Func.resolve_expression``
      delegates to per operand (expressions
      .py:694-699) -- on the WRITTEN operand,
      never by inspecting the modeled
      function's answer. Each operand class
      decides for itself: an ``F`` becomes a
      ``Col`` (has as_sql), while
      ``OuterRef`` over a nested ``OuterRef``
      hands back its inner name, a bare
      ``OuterRef`` with NO as_sql
      (expressions.py:645-648)                ->  ``operand_resolution_usable``
    what putting a CONDITION that restricts
      something through resolution came back
      with (aggregates.py:53's
      ``c.filter.resolve_expression`` -- a
      DIFFERENT callee dispatched on the
      condition's own class): a ``Q`` becomes
      a ``WhereNode`` and an ``Exists`` stays
      an ``Exists`` (both have as_sql), while
      ``OuterRef`` over a nested ``OuterRef``
      hands back a bare ``OuterRef`` and
      ``MultiColSource`` hands back itself,
      neither with an as_sql. Where NO such
      step runs -- no condition, or one
      LEFT AS WRITTEN, whose falsiness
      short-circuits ``:53``'s ``and`` --
      there is no outcome to hold against
      the aggregation, so the flag is True:
      the neutral element of the
      conjunction the modeled function
      forms, leaving the answer to the
      other two inputs                    ->  ``condition_resolution_usable``
    every part that must resolve resolves:
      the operand names a real field, the
      restricting condition does, an
      expression-valued default does, and
      -- ONLY when a default is supplied --
      the aggregate's own output type can be
      determined                              ->  ``parts_resolve``

  returned real expression                    ->  model output
    ``FieldError`` raised                     ->  ``ResolutionRefused``
    ``bool(result.is_summary)``               ->  ``is_final_aggregation``
    ``isinstance(result, Coalesce)``          ->  ``supplies_fallback``
    ``result.default is not None``            ->  ``holds_own_fallback``
    every source expression of the result,
      and the condition restricting it if it
      has one, is in resolved form -- i.e.
      has an ``as_sql`` (``_parts_usable``)  ->  ``parts_usable``
    source expression #0 of the Coalesce      ->  ``wrapped``
      * ``_parts_usable`` of THAT source        ->  ``Result().wrapped.
                                                  parts_usable``
    source expression #1 of the Coalesce      ->  ``fallback`` of the result
      * it IS the written value: for an
        expression, ``s1 is default``; for a
        plain value, the wrapper Coalesce
        builds for it carries that very
        object (``s1.value is default`` for a
        ``Value``, ``s1.name is default`` for
        the ``F`` a str becomes)             ->  ``Result().fallback is fallback``
      * ``hasattr(s1,'as_sql')``              ->  ``Result().fallback.usable``
      * ``s1 is not default``, and ``s1`` IS
        the object aggregates.py:66's
        delegated ``default.resolve_
        expression`` handed back -- read from
        that call, never compared against a
        re-resolution, so a class with no
        structural equality is judged the
        same way as every other               ->  ``Result().fallback.
                                                  resolution_of is fallback``

Note the fallback bridge is ``is None``, not truthiness: falsy defaults (``0``,
``0.0``, ``False``, ``''``) are generated and DO take the fallback branch in the
real code, so a shadow keyed on truthiness would be refuted here.

The last three rows are the point of this gate for this cell. "The supplied
fallback is the RESOLVED one" is not a flag anyone reports -- it is the identity
of the Coalesce's second source expression, taken against the written object
itself (``is``) and against WHAT THE DELEGATED CALL HANDED BACK, recorded from
that call rather than reconstructed by re-resolving and comparing. Equality is
the obvious reading of it and it is the wrong one: ``__eq__`` and ``identity``
live on ``Expression`` (expressions.py:392-422), while ``Subquery(BaseExpression,
Combinable)`` (expressions.py:1141) and its ``Exists`` subclass inherit
``object.__eq__``, so a re-resolution of the very same written default never
compares equal to the one the real callee supplied, and the provenance edge
would read as ABSENT on a realization where the callee does establish it.
Reading the call's outcome is one test for every class in the hierarchy, and the
space realizes both kinds. A shadow that supplied the written value, or a value
derived from anything else, or one that is not compilable, disagrees on a real
input.

THIRD LEG: the wrapper is born unmarked
---------------------------------------
``wrapper = Expression(False, True)`` would be untestable through the return
value alone -- the next line overwrites the ``False``. So on every fallback
probe the check also reconstructs a fresh wrapper from the real returned
``Coalesce``'s own source expressions (``Coalesce(*result.get_source_
expressions())``) and requires ``is_summary is False``, matching the model's
``Expression(False, True)`` and the ``Assert`` that was stripped from the
shadow. This is what makes a pre-patch oracle fail this script: without
``coalesce.is_summary = c.is_summary`` the returned wrapper stays at that
born-unmarked ``False`` while the shadow reports ``requested_final``, so every
``summarize=True`` + ``default=`` probe disagrees.

FOURTH LEG: the written default is left as it was
-------------------------------------------------
After every probe with an expression-valued default the check re-reads the
WRITTEN default object and requires that it is still not the resolution of
anything and still exactly as compilable as it arrived -- the concrete form of
the model's ``fallback.usable == Old(fallback.usable)`` and
``fallback.resolution_of is None``. An in-place resolution would be invisible
in the return value and is caught here.

INPUTS
------
The enumeration is over the CONCRETE realization space -- aggregate kind x
source expression (plain field / composed / mixed-type / aggregate-containing /
nonexistent) x default kind (plain ints/floats/bools/strings, expression-valued
compilable and not, and a default over a nonexistent reference) x filter
(including one that does not resolve) x distinct x summarize -- exhaustively,
and then fuzzed over that same space with a pinned seed to reach the >= 1e5
budget. Every branch of the impl region is exercised (both rejection raises,
early return, fallback return, both ``fallback_is_expression`` values, both
``usable`` values of an expression-valued default), and coverage of all of
those, of both rejection causes, and of the ASYMMETRIC third rejection cause
(a mixed-type aggregate is PRODUCED with no default and REJECTED with one) is
ASSERTED at the end, so the script cannot pass vacuously.

Pinned seed: 15375 (recorded in mapping.md, ## G-CONF). Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs and exits 1.
stdlib + django only.
"""
import json
import random
import sys

SEED = 15375
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# SHADOW: model.py, contract calls stripped, otherwise verbatim.
# ---------------------------------------------------------------------------

class ResolutionRefused(Exception):
    pass


class FallbackValue:
    def __init__(self, usable):
        self.usable = usable
        self.resolution_of = None


class Expression:
    def __init__(self, is_final_aggregation, supplies_fallback):
        self.is_final_aggregation = is_final_aggregation
        self.supplies_fallback = supplies_fallback
        self.holds_own_fallback = False
        self.parts_usable = False
        self.fallback = None
        self.wrapped = None


def resolve_aggregation(requested_final, fallback, fallback_is_expression,
                        resolution_yields_distinct, resolution_yield,
                        aggregating_operand, operand_resolution_usable,
                        condition_resolution_usable,
                        vacuous_condition, parts_resolve):
    # (verbatim from model.py's impl region; only Assert(...) removed)
    # impl-start
    if not parts_resolve:
        # A part this resolution has to resolve cannot be resolved against the
        # query at all, so no expression is produced for the aggregation.
        raise ResolutionRefused()
    # The unchanged base resolution stamps the requested final-flag onto the
    # resolved aggregation; the aggregation does not itself supply a fallback,
    # and it still holds the fallback value the caller asked for.
    c = Expression(requested_final, False)
    # Resolving the aggregation puts the parts it is built from through
    # resolution: the operand it aggregates over, and the condition restricting it
    # WHEN that condition restricts anything. Each of those is handed off, and what
    # each comes back with — usable as it stands or not — is READ here, not
    # decided. A condition that restricts nothing is left as written. So the
    # aggregation is usable as it stands exactly when all three came out that way.
    # This is the step whose omission leaves a correctly flagged aggregation that
    # was never actually resolved.
    c.parts_usable = (operand_resolution_usable and condition_resolution_usable
                      and not vacuous_condition)
    # MODELLED STATE, not a step of the work: a resolved aggregation for which a
    # fallback value was requested DOES still hold that value at this point —
    # resolution reads the value off the resolved aggregation and only clears it
    # below, before the returned expression takes over supplying it. A model that
    # drops this line claims the aggregation never holds a fallback of its own,
    # which is false of the real callee; and such a model can no longer describe
    # leaving the fallback in place while wrapping, which is the behaviour the
    # clearing exists to prevent.
    c.holds_own_fallback = fallback is not None
    if aggregating_operand and not requested_final:
        # The resolved aggregation aggregates over another aggregation and a
        # non-final resolution was requested: rejected, no expression produced.
        raise ResolutionRefused()
    if fallback is None:
        return c
    supplied = fallback
    if fallback_is_expression:
        # The requested fallback value is itself an expression, so it is put
        # through resolution and what THAT yielded is what gets supplied. This
        # resolution hands that step off and does not decide its outcome, so the
        # outcome is READ here: the value that came back is what the returned
        # expression goes on to supply, whether or not it is usable as it stands.
        # The value as written is left untouched either way.
        if resolution_yields_distinct:
            # A DISTINCT value came back. It is recorded as the resolved form OF
            # the requested one, and its usability is whatever resolving yielded
            # — not something this step may assert.
            resolution_yield.resolution_of = fallback
            supplied = resolution_yield
        else:
            # Resolution handed back the very value it was given: a value already
            # in resolved form is its own resolved form, so that value is what is
            # supplied, exactly as it arrived.
            supplied = fallback
    # A fallback is supplied: return a distinct expression that supplies it. It
    # is built unmarked.
    wrapper = Expression(False, True)
    # (model.py asserts here that a freshly constructed fallback wrapper is
    #  UNMARKED; the stripped Assert is checked against the real repo by
    #  `born_unmarked` in the oracle below, not assumed.)
    # Its parts are the resolved aggregation, which always stands as a part of the
    # expression built over it, and the value it supplies: so all of its parts are
    # usable exactly when that value is.
    wrapper.parts_usable = supplied.usable
    # The returned fallback-supplying expression must carry the same final-flag
    # as the aggregation it supplies the fallback for.
    wrapper.is_final_aggregation = c.is_final_aggregation
    # The aggregation itself no longer holds the fallback value — the returned
    # expression is what supplies it — and it stays reachable from that
    # expression, which is what supplies the fallback FOR it.
    c.holds_own_fallback = False
    wrapper.wrapped = c
    # The value the returned expression supplies is the one resolution arrived
    # at for the requested fallback.
    wrapper.fallback = supplied
    return wrapper
    # impl-end


def shadow_observe(requested_final, fb_obj, fallback_is_expression,
                   resolution_yields_distinct, resolution_yield,
                   aggregating_operand, operand_resolution_usable,
                   condition_resolution_usable,
                   vacuous_condition, parts_resolve):
    """Run the shadow and project it onto the full observable tuple."""
    try:
        r = resolve_aggregation(requested_final, fb_obj, fallback_is_expression,
                                resolution_yields_distinct, resolution_yield,
                                aggregating_operand, operand_resolution_usable,
                                condition_resolution_usable,
                                vacuous_condition, parts_resolve)
    except ResolutionRefused:
        return ("refused",)
    w = r.wrapped
    f = r.fallback
    return (
        "produced",
        bool(r.is_final_aggregation),
        bool(r.supplies_fallback),
        bool(r.holds_own_fallback),
        bool(r.parts_usable),
        w is not None,
        None if w is None else bool(w.is_final_aggregation),
        None if w is None else bool(w.supplies_fallback),
        None if w is None else bool(w.holds_own_fallback),
        None if w is None else bool(w.parts_usable),
        f is not None,
        None if f is None else (f is fb_obj),
        None if f is None else bool(f.usable),
        None if f is None else (f.resolution_of is fb_obj),
    )


# ---------------------------------------------------------------------------
# ORACLE: the real patched Aggregate.resolve_expression.
# ---------------------------------------------------------------------------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


_MODEL = {}


def _build_model():
    """A minimal real model giving the aggregates real fields to resolve over.
    Piggy-backs on the registered "contenttypes" app label."""
    from django.db import models

    class Widget(models.Model):
        num = models.IntegerField()
        rating = models.FloatField()
        name = models.CharField(max_length=20)

        class Meta:
            app_label = "contenttypes"

    _MODEL["Widget"] = Widget
    _MODEL["query"] = Widget.objects.all().query


def oracle_observe(kind, source, default, distinct, filt, summarize,
                   src_extra=None):
    """CALL the real patched Aggregate.resolve_expression on one concrete
    realization. Returns (observable_tuple, born_unmarked, written_intact).

      observable_tuple  same shape as shadow_observe's
      born_unmarked     None on the no-fallback / refused path, else whether a
                        fresh wrapper over the returned wrapper's own sources
                        carries is_summary False (model.py's
                        Expression(False, True) / the stripped Assert)
      written_intact    None unless the default is an expression, else whether
                        the WRITTEN default object is still exactly as
                        compilable as it arrived and is still not the
                        resolution of anything reachable here (the concrete
                        form of fallback.usable == Old(fallback.usable) and
                        fallback.resolution_of is None)
    """
    from django.core.exceptions import FieldError
    from django.db.models import F, Value
    from django.db.models.functions import Coalesce

    kwargs = dict(src_extra or {})
    if default is not _NO_DEFAULT:
        kwargs["default"] = default
    if distinct:
        kwargs["distinct"] = True
    if filt is not None:
        kwargs["filter"] = filt

    is_expr = hasattr(default, "resolve_expression")
    usable_before = hasattr(_as_coalesce_arg(default), "as_sql")

    agg = kind(source, **kwargs)
    # WHAT THE DELEGATED CALL ON THE WRITTEN DEFAULT HANDED BACK -- recorded from
    # that call, not reconstructed after it. "is the resolution of the written
    # value" is a claim about PROVENANCE, and the only a-posteriori way to test it
    # is equality against a re-resolution, which answers "no" for every class that
    # implements no structural equality whatever the real callee did. `Subquery`
    # is exactly that case: `__eq__`/`identity` live on `Expression`
    # (expressions.py:392-422), while `Subquery(BaseExpression, Combinable)`
    # (expressions.py:1141) and its `Exists` subclass inherit `object.__eq__`, so a
    # re-resolution of the very same written object never compares equal and the
    # provenance edge would read as ABSENT on a realization where the real callee
    # does establish it. So the outcome of aggregates.py:66's delegated
    # `default.resolve_expression` is READ: the method is wrapped on the written
    # value's own class for the duration of the call and records, for THAT object,
    # what the real method returned -- which it also returns unchanged, so nothing
    # about the callee's behaviour differs. Identity against that, and the same
    # test applies to every class in the hierarchy.
    resolved_yield = []
    traced_cls = None
    if is_expr:
        traced_cls = type(default)
        _orig_resolve = traced_cls.resolve_expression
        _had_own = "resolve_expression" in traced_cls.__dict__

        def _record_resolve(self, *a, **kw):
            out = _orig_resolve(self, *a, **kw)
            if self is default:
                resolved_yield.append(out)
            return out

        traced_cls.resolve_expression = _record_resolve
    # >>> the real repo function under conformance (aggregates.py:50) <<<
    try:
        try:
            result = agg.resolve_expression(_MODEL["query"], True, None,
                                            summarize)
        finally:
            if traced_cls is not None:
                if _had_own:
                    traced_cls.resolve_expression = _orig_resolve
                else:
                    del traced_cls.resolve_expression
    except FieldError:
        # No expression is produced for this aggregation at all.
        written_intact = None
        if is_expr:
            written_intact = (hasattr(default, "as_sql") == usable_before)
        return ("refused",), None, written_intact

    supplies = isinstance(result, Coalesce)
    born_unmarked = None
    written_intact = None
    w = s1 = None
    if supplies:
        srcs = result.get_source_expressions()
        w, s1 = srcs[0], srcs[1]
        born_unmarked = Coalesce(*srcs).is_summary is False

    if is_expr:
        # FOURTH LEG: the written default object must be untouched.
        written_intact = (hasattr(_as_coalesce_arg(default), "as_sql")
                          == usable_before)

    def _is_written(s):
        if s is None:
            return None
        if is_expr:
            return s is default
        # A plain value is carried through the wrapper Coalesce builds for it,
        # which holds THAT VERY OBJECT (see Func._parse_expressions).
        if isinstance(s, Value):
            return s.value is default
        if isinstance(s, F):
            return s.name is default
        return False

    def _is_resolution_of_written(s):
        if s is None:
            return None
        if not is_expr:
            # Nothing was derived from a value that needed no resolution.
            return False
        if s is default:
            return False
        # Identity against what the delegated call handed back for this very
        # object (see the trace installed around the real call), rather than
        # equality against a re-resolution: the latter is unanswerable for a
        # class that implements no structural equality, and would report the
        # provenance edge missing on a realization where it is present.
        return any(s is y for y in resolved_yield)

    tup = (
        "produced",
        bool(result.is_summary),
        supplies,
        getattr(result, "default", None) is not None,
        _parts_usable(result),
        w is not None,
        None if w is None else bool(w.is_summary),
        None if w is None else isinstance(w, Coalesce),
        None if w is None else (getattr(w, "default", None) is not None),
        _parts_usable(w),
        s1 is not None,
        _is_written(s1),
        None if s1 is None else hasattr(s1, "as_sql"),
        _is_resolution_of_written(s1),
    )
    return tup, born_unmarked, written_intact


# ---------------------------------------------------------------------------
# Realization space (concrete -> abstract).
# ---------------------------------------------------------------------------

def _as_coalesce_arg(value):
    """The written default AS THE FALLBACK-SUPPLYING EXPRESSION REPRESENTS IT.
    Mirrors Func._parse_expressions (expressions.py:184-189), which the Coalesce
    constructor applies to whatever it is handed: an expression is taken as is, a
    str becomes an F (a field REFERENCE, which has no as_sql), and any other plain
    value becomes a Value (which has). This is a property of the WRITTEN input, so
    computing it here is not an oracle echo -- and it is why the model admits a
    non-expression fallback value that is NOT usable as it stands (a str), which a
    precondition demanding usability would have excluded."""
    if hasattr(value, "resolve_expression"):
        return value
    from django.db.models import F, Value
    return F(value) if isinstance(value, str) else Value(value)


def _has_structural_equality(value):
    """The written value's class compares by VALUE rather than by object identity.

    An A-PRIORI property of the class, read off the class itself: `Expression`
    defines `identity` and `__eq__` (expressions.py:392-422), so two separate
    writings of the same `Value`/`Lower`/`F` compare equal, while
    `Subquery(BaseExpression, Combinable)` (expressions.py:1141) and `Exists`
    inherit `object.__eq__` and compare only by identity.

    Nothing in the modeled function depends on this -- the real callee treats an
    `Exists` default exactly as it treats a `Lower`. It is here only so the
    coverage assertions can require that the provenance leg be realized on BOTH
    kinds of class, which is what keeps an equality-based recognizer of that leg
    from passing unrefuted."""
    return type(value).__eq__ is not object.__eq__


def _parts_usable(expr):
    """EVERY PART this real expression is built from can be used as it stands.

    The concrete form of the model's ``Expression.parts_usable``: each source
    expression of ``expr``, and the condition restricting it if it has one, must
    be in resolved, compilable form -- i.e. have an ``as_sql``. This is the same
    predicate ``fallback.usable`` applies to one value (mapping.md §2), lifted to
    the parts an expression is built out of.

    It is what distinguishes the aggregation resolution actually RESOLVED from a
    freshly built one carrying the same final-flag: a bare
    ``Func.resolve_expression`` resolves the operands but NOT the condition
    (that is ``aggregates.py:53``, one line further on), leaving a raw ``Q``,
    which has no ``as_sql``."""
    if expr is None:
        return None
    for src in expr.get_source_expressions():
        if src is not None and not hasattr(src, "as_sql"):
            return False
    filt = getattr(expr, "filter", None)
    if filt is not None and not hasattr(filt, "as_sql"):
        return False
    return True


def _multi_col_source():
    """A real MultiColSource over the probe model's own field. Its
    `resolve_expression` is `return self` (fields/related_lookups.py:25-26) and it
    has no `as_sql`, so it realizes a resolving step that hands back the very
    value it was given whose yield is NOT usable as it stands."""
    from django.db.models.fields.related_lookups import MultiColSource
    field = _MODEL["Widget"]._meta.get_field("num")
    return MultiColSource("probe_alias", (field,), (field,), field)


def _empty_wherenode():
    """A childless `WhereNode`. FALSY (`django/utils/tree.py:60-62`), so
    `aggregates.py:53`'s `and` short-circuits and it is LEFT AS WRITTEN exactly as
    an empty `Q` is -- but `WhereNode` defines `as_sql`
    (`django/db/models/sql/where.py:65`), so the aggregation it restricts stays
    usable as it stands. It is the near-miss control on the other side of the
    COMPILABILITY boundary from `emptyQ`, and the realization on which a
    falsiness-only reading of `vacuous_condition` disagrees with the real callee
    (measured: `Sum('num', filter=Q())` -> `parts_usable False`, `Sum('num',
    filter=WhereNode())` -> `parts_usable True`).

    Reachable from public ORM input, not hand-built: `Q.resolve_expression`
    returns a `WhereNode` (`query_utils.py:71-77`), so `:53` rewrites `c.filter`
    from `Q` to `WhereNode`, and `Query.resolve_expression` re-resolves every
    annotation when a queryset is used as a subquery (`sql/query.py:1057-1061`).
    Resolving `Sum('num', filter=Q(Q()), default=0)` -- a TRUTHY `Q` whose
    resolved form is a CHILDLESS `WhereNode` -- inside a `Subquery` therefore
    hands this very shape to the modeled function on the second resolution
    (measured on both the base and the patched image)."""
    from django.db.models.sql.where import WhereNode
    return WhereNode()


class _NoDefault:
    def __repr__(self):
        return "<no default>"


_NO_DEFAULT = _NoDefault()


def _spaces():
    """The concrete realization space, built after django.setup().

    Each source and default carries the a-priori facts the bridge needs:
      sources:  (name, expr, contains_aggregate, resolves, output_type_known,
                 operand_resolution_usable, extra_kwargs)
      defaults: (name, value, resolves)
    """
    from django.db.models import (
        Avg, Count, Exists, F, IntegerField, Max, Min, OuterRef, Q, StdDev,
        Subquery, Sum, Value, Variance,
    )
    from django.db.models.expressions import Ref
    from django.db.models.functions import Abs, Lower

    # (name, class, allows_default, allows_distinct)
    kinds = [
        ("Sum", Sum, True, False),
        ("Avg", Avg, True, False),
        ("Min", Min, True, False),
        ("Max", Max, True, False),
        ("StdDev", StdDev, True, False),
        ("Variance", Variance, True, False),
        # Count forbids `default` (empty_result_set_value is not None), so it
        # only realizes the no-fallback branch -- which it does cover.
        ("Count", Count, False, True),
    ]
    sources = [
        # name, expr, contains_aggregate, resolves, output_type_known, op_usable.
        # `op_usable` is an A-PRIORI property of the WRITTEN operand's own class:
        # what `arg.resolve_expression` (the step Func.resolve_expression delegates
        # to per operand, expressions.py:694-699) comes back with -- whether that
        # resolved form has an `as_sql`. For almost every operand it does; the
        # nested-OuterRef family below is the realizable exception.
        ("num", "num", False, True, True, True, None),
        ("rating", "rating", False, True, True, True, None),
        ("name", "name", False, True, True, True, None),
        ("f_mul", F("num") * 2, False, True, True, True, None),
        ("lower", Lower("name"), False, True, True, True, None),
        # the operand itself contains an aggregate -> aggregating_operand
        ("agg_sum", Sum("num"), True, True, True, True, None),
        # mixed operand types: the aggregate resolves, but its OWN output type
        # cannot be determined -- which only matters when a fallback is
        # supplied (aggregates.py:68 asks for it only there).
        ("mixed", F("num") + F("name"), False, True, False, True, None),
        # names no field at all -> nothing to resolve against
        ("nofield", "nope", False, False, True, True, None),
        ("f_nofield", F("nope"), False, False, True, True, None),
        # OPERANDS WHOSE RESOLUTION COMES BACK WITH SOMETHING NOT USABLE AS IT
        # STANDS. `OuterRef.resolve_expression` returns its inner name unchanged
        # when that name is itself an `OuterRef` (expressions.py:645-648), so the
        # resolved aggregation carries a bare `OuterRef` with NO `as_sql` and cannot
        # be compiled -- while nothing raised, so this is NOT a rejection. Its own
        # output type cannot be determined either: `Aggregate.get_source_fields`
        # (aggregates.py:38) reads `_output_field_or_none` off each operand, which a
        # bare `OuterRef` also lacks, so the fallback path -- which is the only path
        # that asks (aggregates.py:68) -- refuses. Realized at two nesting depths so
        # the fact is not carried by one object's identity.
        # Written WITH an explicit output_field, which is what keeps the aggregate's
        # OWN output type determinable: `Aggregate.get_source_fields`
        # (aggregates.py:38) reads `_output_field_or_none` off each operand, which a
        # bare `OuterRef` lacks, so WITHOUT the explicit field the fallback path --
        # the only path that asks (aggregates.py:68) -- dies on an AttributeError
        # rather than resolving or rejecting. With it, both paths PRODUCE, and the
        # parts-usable equality is exercised on the bare return AND through the
        # wrapper. Both spellings are ordinary ORM usage.
        ("outerref2", OuterRef(OuterRef("num")), False, True, True, False,
         {"output_field": IntegerField()}),
        ("outerref3", OuterRef(OuterRef(OuterRef("num"))), False, True, True,
         False, {"output_field": IntegerField()}),
        # the near-miss control on the other side of the boundary: a PLAIN OuterRef
        # resolves to a ResolvedOuterRef, which HAS an `as_sql`, so the operand IS
        # usable as it stands and the aggregation's parts-usable flag must come out
        # the same as for a plain field. This keeps the operand leg keyed on what the
        # resolution came back with rather than on the OuterRef family as such.
        ("outerref1", OuterRef("num"), False, True, True, True,
         {"output_field": IntegerField()}),
    ]
    # `default` kinds. The plain values are NOT expressions
    # (hasattr(d, 'resolve_expression') is False -> fallback_is_expression
    # False); the expression values are. Falsy-but-not-None values are
    # included deliberately: the real bridge is `is None`. `expr_f` /
    # `expr_combined` are NOT compilable as written (no as_sql) while
    # `expr_value_*` / `expr_lower` / `expr_abs` are, so both `usable` values
    # of an expression-valued fallback are realized.
    defaults = [
        ("none", _NO_DEFAULT, True),    # -> no fallback requested
        ("int_zero", 0, True),          # falsy, still wraps
        ("int_neg", -7, True),
        ("int_big", 10 ** 9, True),
        ("float", 2.5, True),
        ("float_zero", 0.0, True),      # falsy, still wraps
        ("bool_false", False, True),    # falsy, still wraps
        ("str_empty", "", True),         # falsy, still wraps
        ("str", "zz", True),
        ("expr_value_int", Value(0), True),
        ("expr_value_str", Value("a"), True),
        ("expr_f", F("num"), True),
        ("expr_combined", Value(1) + Value(2), True),
        ("expr_lower", Lower(Value("AB")), True),
        ("expr_abs", Abs(Value(-3)), True),
        # an expression-valued default that does NOT resolve
        ("expr_f_nofield", F("nope"), False),
        # Expression-valued defaults whose RESOLUTION HANDS BACK THE VERY OBJECT
        # it was given: a value already in resolved form is its own resolved
        # form, so no distinct value is produced. `Ref.resolve_expression` is
        # `return self` (expressions.py:902-905) and its yield IS usable;
        # `MultiColSource.resolve_expression` likewise (fields/related_lookups.py
        # :25-26) and its yield is NOT. Without these the space realizes only the
        # distinct-yield arm and the other arm of the resolution branch is never
        # exercised.
        ("expr_ref", Ref("agg", Sum("num")), True),
        ("expr_multicol", _multi_col_source(), True),
        # ... and one whose resolution DOES yield a distinct value that still
        # cannot be used as it stands: OuterRef over a nested OuterRef hands back
        # its inner name, a bare OuterRef with no as_sql (expressions.py:645-648).
        ("expr_outerref2", OuterRef(OuterRef("num")), True),
        # the near-miss control on the other side: a plain OuterRef resolves to a
        # ResolvedOuterRef, which is distinct AND usable.
        ("expr_outerref", OuterRef("num"), True),
        # ... and two whose CLASS IMPLEMENTS NO STRUCTURAL EQUALITY: `Subquery`
        # extends `BaseExpression`, not `Expression` (expressions.py:1141), and
        # `Exists` extends `Subquery`, so `==` on either is `object.__eq__`.
        # Resolving them yields a distinct, compilable object exactly as
        # resolving a `Lower` does, and the real callee supplies THAT object --
        # but a recognizer that tested the provenance by comparing against a
        # re-resolution would answer "not the resolution of the written value"
        # here no matter what the callee did. Without these rows the provenance
        # leg is realized only on classes carrying structural equality, so such a
        # recognizer would pass 1e5 inputs. Both spellings, so the coverage is
        # not carried by one class's identity.
        ("expr_subquery",
         Subquery(_MODEL["Widget"].objects.all().values("num")[:1]), True),
        ("expr_exists", Exists(_MODEL["Widget"].objects.all()), True),
    ]
    # (name, q, resolves, vacuous). `vacuous` is an A-PRIORI property of the
    # WRITTEN condition, declared here and recomputed from the written object in
    # the bridge: it is present, it was LEFT AS WRITTEN -- it has no children and
    # is therefore FALSY (django/utils/tree.py:60-62), so aggregates.py:53's `and`
    # short-circuits and never resolves it -- AND its written form has no
    # `as_sql`, so leaving it alone left an unresolved part behind. Realized four
    # ways (a bare empty Q, a negated empty Q, and both binary combinations of
    # empties) so the flag is not carried by one object's identity, plus the two
    # near-miss controls, one on each side of it: the TRUTHY-but-empty-valued
    # `pk__in=[]` across the falsiness boundary, and the childless `WhereNode`
    # across the COMPILABILITY boundary -- equally falsy, equally left as
    # written, but usable as it stands, so `vacuous` is False for it.
    filters = [
        ("nofilter", None, True, False),
        ("filter", Q(num__gt=1), True, False),
        ("badfilter", Q(nope__gt=1), False, False),
        ("emptyQ", Q(), True, True),
        ("negEmptyQ", ~Q(), True, True),
        ("andEmptyQ", Q() & Q(), True, True),
        ("orEmptyQ", Q() | Q(), True, True),
        ("truthyEmptySet", Q(pk__in=[]), True, False),
        # LEFT AS WRITTEN, like the four empties above -- childless, hence FALSY,
        # so aggregates.py:53's `and` short-circuits and it is never replaced by a
        # resolved condition -- but it HAS an `as_sql`
        # (django/db/models/sql/where.py:65), so the aggregation it restricts is
        # usable as it stands and `vacuous_condition` is False. Without this row
        # the space realizes being left as written ONLY where that coincides with
        # being uncompilable, and a falsiness-only reading of the input passes
        # 1e5 inputs while diverging from the real callee here.
        ("emptyWhereNode", _empty_wherenode(), True, False),
        # A condition that DOES restrict something and resolves WITHOUT raising,
        # but whose delegated resolution (aggregates.py:53) comes back with
        # something that has NO `as_sql`: `OuterRef.resolve_expression` returns its
        # inner name unchanged when that name is itself an `OuterRef`
        # (expressions.py:645-648). Realizable from user-facing ORM code -- `filter=`
        # is not restricted to `Q` (Aggregate.__init__ just stores it,
        # aggregates.py:32) and a nested OuterRef inside a doubly-nested Subquery is
        # ordinary usage. This is the condition-leg counterpart of the `outerref2`
        # operand, and without it the condition leg of the parts-usable equality is
        # only half exercised.
        ("nestedOuterRefFilter", OuterRef(OuterRef("num")), True, False),
        # ... and a second spelling of the same outcome, so the leg is not carried
        # by one object's identity: MultiColSource.resolve_expression is
        # `return self` (fields/related_lookups.py:25-26) and it has no `as_sql`.
        ("multiColFilter", _multi_col_source(), True, False),
    ]
    return kinds, sources, defaults, filters


def enumerate_space(kinds, sources, defaults, filters):
    """Exhaustive enumeration of the concrete realization space."""
    cases = []
    for kname, kcls, allows_default, allows_distinct in kinds:
        for src in sources:
            for dflt in defaults:
                if dflt[1] is not _NO_DEFAULT and not allows_default:
                    continue
                for filt in filters:
                    for distinct in ((False, True) if allows_distinct else (False,)):
                        for summarize in (True, False):
                            cases.append((kname, kcls, src, dflt, distinct,
                                          filt, summarize))
    return cases


def check(case):
    """Diff shadow against the real patched function on one realization.
    Returns (error string or None, coverage key or None)."""
    kname, kcls, src, dflt, distinct, filt, summarize = case
    (sname, source, contains_agg, src_resolves, out_type_known,
     op_usable, src_extra) = src
    dname, default, dflt_resolves = dflt
    fname, filt_q, filt_resolves, filt_vacuous = filt

    # --- bridge: concrete realization -> the model's inputs (a priori: read
    #     off the WRITTEN construction, never off the oracle's answer) ---
    requested_final = bool(summarize)
    has_fallback = default is not _NO_DEFAULT and default is not None
    fallback_is_expression = hasattr(default, "resolve_expression")
    usable = hasattr(_as_coalesce_arg(default), "as_sql")
    fb_obj = FallbackValue(usable) if has_fallback else None
    # WHAT RESOLVING THE WRITTEN VALUE YIELDS. This is the outcome of a
    # DIFFERENT callee -- `default.resolve_expression`, the step aggregates.py:66
    # hands off to -- so it is obtained by calling THAT callee on the WRITTEN
    # object, never by inspecting the modeled function's answer. Each expression
    # class decides for itself: most build a new object (`c = self.copy()`,
    # expressions.py:246), while a value already in resolved form hands back the
    # very object it was given (`return self` -- Ref, expressions.py:902-905;
    # MultiColSource, fields/related_lookups.py:25-26; OuterRef over a nested
    # OuterRef, expressions.py:645-648, returns its inner name). The yield's own
    # usability is likewise that callee's outcome, not this one's.
    resolution_yields_distinct = False
    resolution_yield = None
    if has_fallback and fallback_is_expression and dflt_resolves:
        _y = default.resolve_expression(_MODEL["query"], True, None, summarize)
        resolution_yields_distinct = _y is not default
        resolution_yield = (FallbackValue(hasattr(_y, "as_sql"))
                            if resolution_yields_distinct else fb_obj)
    aggregating_operand = contains_agg
    # WHAT PUTTING THE OPERAND THROUGH RESOLUTION CAME BACK WITH. This is the
    # outcome of a DIFFERENT callee -- `written_operand.resolve_expression`, the
    # step `Func.resolve_expression` delegates to per operand (expressions.py
    # :694-699) -- so it is read off the WRITTEN operand's own class, never by
    # inspecting the modeled function's answer. Each operand class decides for
    # itself: an `F`/str becomes a `Col` and a `Value` stays a `Value` (both have
    # `as_sql`), while `OuterRef.resolve_expression` returns its inner name
    # unchanged when that name is itself an `OuterRef` (expressions.py:645-648),
    # handing back a bare `OuterRef` with NO `as_sql`. Carried as an a-priori fact
    # of the space so that operands which do not resolve at all -- where the step
    # raises instead of coming back -- still have a defined value.
    operand_resolution_usable = op_usable
    # THE AGGREGATION IS RESTRICTED BY A CONDITION THAT WAS LEFT AS WRITTEN AND
    # CANNOT BE USED AS IT STANDS. Computed from the WRITTEN condition alone --
    # its falsiness, which is what makes aggregates.py:53's `and` short-circuit so
    # that no resolving step runs on it, AND the absence of an `as_sql` on that
    # written form -- never off the oracle's answer. BOTH halves are needed: a
    # childless `WhereNode` is FALSY too, so `:53` short-circuits on it as well,
    # yet it HAS an `as_sql` and the aggregation it restricts stays usable as it
    # stands, so a falsiness-only reading would send two realizations the real
    # callee treats differently to one abstract input. The declared column is
    # cross-checked against the written object so it cannot drift. A condition
    # left as written is never resolved, so it cannot FAIL to resolve either:
    # vacuity and non-resolvability stay disjoint by construction of the space.
    vacuous_condition = (filt_q is not None and not filt_q
                        and not hasattr(filt_q, "as_sql"))
    if vacuous_condition != filt_vacuous:
        raise AssertionError(
            "realization %r declares vacuous=%r but the WRITTEN condition gives "
            "%r (falsy=%r, has as_sql=%r)"
            % (fname, filt_vacuous, vacuous_condition,
               filt_q is not None and not filt_q, hasattr(filt_q, "as_sql")))
    # WHAT PUTTING THE CONDITION THROUGH RESOLUTION CAME BACK WITH. Like the
    # operand leg and the fallback-value leg, this is the outcome of a DIFFERENT
    # callee -- `written_condition.resolve_expression`, the step aggregates.py:53
    # hands off to -- so it is obtained by CALLING that callee on the WRITTEN
    # condition, never by inspecting the modeled function's answer. Each condition
    # class decides for itself: a `Q` becomes a `WhereNode` and an `Exists` stays
    # an `Exists` (both have `as_sql`), while `OuterRef.resolve_expression` returns
    # its inner name unchanged when that name is itself an `OuterRef`
    # (expressions.py:645-648) and `MultiColSource.resolve_expression` is
    # `return self` (fields/related_lookups.py:25-26) -- neither has an `as_sql`.
    # Where NO step runs at all -- no condition, or one LEFT AS WRITTEN, whose
    # falsiness short-circuits `:53`'s `and` -- there is no outcome to hold
    # against the aggregation, so the flag is True: the neutral element of the
    # conjunction the modeled function forms, which leaves the answer to the two
    # other inputs. Not unread there, though: a childless `WhereNode` is left as
    # written and yet usable as it stands, so vacuity does not carry the answer
    # for it, and this flag is what says the aggregation's parts are in order.
    condition_resolution_usable = True
    if filt_q is not None and filt_q and filt_resolves:
        _cy = filt_q.resolve_expression(_MODEL["query"], True, None, summarize)
        condition_resolution_usable = hasattr(_cy, "as_sql")
    parts_resolve = (src_resolves and filt_resolves
                     and (dflt_resolves or not has_fallback)
                     and (out_type_known or not has_fallback))

    shadow = shadow_observe(requested_final, fb_obj, fallback_is_expression,
                            resolution_yields_distinct, resolution_yield,
                            aggregating_operand, operand_resolution_usable,
                            condition_resolution_usable,
                            vacuous_condition, parts_resolve)
    oracle, born_unmarked, written_intact = oracle_observe(
        kcls, source, default, distinct, filt_q, summarize, src_extra)

    desc = ("kind=%s source=%s default=%s(%r) distinct=%r %s summarize=%r\n"
            "  model input: requested_final=%r fallback=%s "
            "fallback_is_expression=%r usable=%r aggregating_operand=%r "
            "vacuous_condition=%r parts_resolve=%r"
            % (kname, sname, dname, default, distinct, fname, summarize,
               requested_final, "None" if fb_obj is None else "<value>",
               fallback_is_expression, usable, aggregating_operand,
               vacuous_condition, parts_resolve))

    if shadow != oracle:
        return ("DISAGREEMENT on %s\n"
                "  shadow (model.py impl region): %r\n"
                "  oracle (real patched Aggregate.resolve_expression): %r"
                % (desc, shadow, oracle)), None

    # Third leg: the model builds the wrapper UNMARKED (Expression(False,
    # True)) before propagating. Refute that against the real wrapper.
    if shadow[0] == "produced" and has_fallback and born_unmarked is not True:
        return ("DISAGREEMENT on %s\n"
                "  shadow (model.py impl region): a freshly constructed "
                "fallback wrapper is UNMARKED (Expression(False, True))\n"
                "  oracle (real repo): a fresh Coalesce over the returned "
                "wrapper's own sources reports is_summary not False "
                "(born_unmarked=%r)" % (desc, born_unmarked)), None

    # Fourth leg: the WRITTEN fallback value is left exactly as it was.
    if fallback_is_expression and written_intact is not True:
        return ("DISAGREEMENT on %s\n"
                "  shadow (model.py impl region): the value as written is left "
                "exactly as it was (fallback.usable == Old(fallback.usable), "
                "fallback.resolution_of is None)\n"
                "  oracle (real repo): the written default object changed "
                "(written_intact=%r)" % (desc, written_intact)), None

    key = (shadow[0], shadow[1:10], shadow[10:], fallback_is_expression, usable,
           parts_resolve, aggregating_operand, sname == "mixed",
           vacuous_condition,
           # whether the resolving step this resolution hands off to yielded a
           # DISTINCT value or handed back the very value it was given, and
           # whether that yield is usable as it stands -- both arms must be
           # realized or the resolution branch is only half exercised.
           (resolution_yields_distinct,
            None if resolution_yield is None else bool(resolution_yield.usable))
           if (has_fallback and fallback_is_expression and parts_resolve)
           else None,
           # slot 10: what putting the operand through resolution came back with.
           # Both outcomes must be realized or the operand leg of the parts-usable
           # equality is only half exercised.
           operand_resolution_usable,
           # slot 11: the same for the CONDITION -- what the delegated condition
           # step (aggregates.py:53) came back with, on the probes where such a
           # step actually runs. Both outcomes must be realized or the condition
           # leg of the parts-usable equality is only half exercised.
           condition_resolution_usable if (filt_q is not None and filt_q
                                           and filt_resolves) else None,
           # slot 12: a condition LEFT AS WRITTEN (falsy, so aggregates.py:53
           # short-circuits) that is ALREADY usable as it stands. The two halves
           # of `vacuous_condition` must be realized APART, or the space ties
           # being left as written to being uncompilable and a falsiness-only
           # reading of that input goes unrefuted over any number of inputs.
           (filt_q is not None and not filt_q
            and hasattr(filt_q, "as_sql")),
           # slot 13: an expression-valued default whose CLASS implements no
           # structural equality, on the arm where resolving it yields a
           # DISTINCT value -- i.e. where the provenance edge is claimed. Unless
           # that is realized, every probe of the provenance leg lands on a
           # class where comparing against a re-resolution happens to work, and
           # a recognizer resting on that is indistinguishable from one that
           # reads what the delegated call returned.
           (has_fallback and fallback_is_expression and parts_resolve
            and resolution_yields_distinct
            and not _has_structural_equality(default)))
    return None, key


def main():
    _setup_django()
    _build_model()
    kinds, sources, defaults, filters = _spaces()

    cases = enumerate_space(kinds, sources, defaults, filters)
    covered = set()
    checked = 0

    # 1. exhaustive over the concrete realization space
    for case in cases:
        err, key = check(case)
        if err:
            print(err)
            print("status=fail")
            return 1
        covered.add(key)
        checked += 1
    n_enumerated = checked

    # 2. seeded fuzz over the SAME space to reach the >= 1e5 budget
    rng = random.Random(SEED)
    while checked < N_FUZZ + n_enumerated:
        case = cases[rng.randrange(len(cases))]
        err, key = check(case)
        if err:
            print(err)
            print("status=fail")
            return 1
        covered.add(key)
        checked += 1

    # 3. anti-vacuity: every branch of the impl region and every observable
    #    outcome must actually have been produced, else the run proved nothing.
    outcomes = {k[0] for k in covered}
    produced = [k for k in covered if k[0] == "produced"]
    final_flags = {k[1][0] for k in produced}
    supplies = {k[1][1] for k in produced}
    fb_facts = {k[2] for k in produced}
    expr_usables = {(k[3], k[4]) for k in covered}
    refuse_causes = {(k[5], k[6]) for k in covered if k[0] == "refused"}
    # the ASYMMETRIC third rejection cause: a mixed-type aggregate is PRODUCED
    # with no fallback and REJECTED with one.
    mixed = {(k[0], k[1][1] if k[0] == "produced" else None)
             for k in covered if k[7]}
    problems = []
    if outcomes != {"produced", "refused"}:
        problems.append("outcomes=%r (want both)" % (sorted(outcomes),))
    if final_flags != {True, False}:
        problems.append("final flags=%r" % (sorted(final_flags),))
    if supplies != {True, False}:
        problems.append("supplies_fallback=%r" % (sorted(supplies),))
    # The new observable must be exercised on BOTH sides: a returned expression
    # all of whose parts are usable as they stand, and one whose supplied value
    # is a field reference the fallback-supplying expression cannot compile.
    parts_flags = {k[1][3] for k in produced}
    if parts_flags != {True, False}:
        problems.append("parts_usable=%r (want both; a written str default is "
                        "passed through as a field reference)"
                        % (sorted(parts_flags),))
    # ... and the aggregation the wrapper supplies a fallback FOR must have had
    # its parts resolved on every probe whose condition restricts something --
    # this is the clause a freshly built, never-resolved aggregation with the
    # right final-flag fails -- while a probe whose condition restricts NOTHING
    # must show the other side, since that condition is never resolved. BOTH
    # sides are required: {True} alone would mean the space never realized a
    # present-but-vacuous condition (the coverage hole this space was widened to
    # close), and {False} alone would mean it never realized a resolved one.
    wrapped_parts_real = {k[1][8] for k in produced
                          if k[1][4] and not k[8] and k[10]
                          and k[11] is not False}
    wrapped_parts_vac = {k[1][8] for k in produced if k[1][4] and k[8]}
    if wrapped_parts_real != {True}:
        problems.append("wrapped aggregation parts_usable=%r on probes whose "
                        "condition restricts something (want {True})"
                        % (sorted(wrapped_parts_real),))
    if wrapped_parts_vac != {False}:
        problems.append("wrapped aggregation parts_usable=%r on probes whose "
                        "condition restricts NOTHING (want {False}: such a "
                        "condition is never resolved)"
                        % (sorted(wrapped_parts_vac),))
    # ... and the wrapped side of the CONDITION leg: a condition that DID restrict
    # something but whose delegated resolution came back unusable leaves the
    # reachable aggregation not usable as it stands either.
    wrapped_parts_cond = {k[1][8] for k in produced
                          if k[1][4] and not k[8] and k[10] and k[11] is False}
    if wrapped_parts_cond != {False}:
        problems.append("wrapped aggregation parts_usable=%r on probes whose "
                        "CONDITION resolution came back NOT usable as it stands "
                        "(want {False})" % (sorted(wrapped_parts_cond),))
    # And the bare-return path likewise, on both sides.
    bare_parts_real = {k[1][3] for k in produced
                       if not k[1][4] and not k[8] and k[10]
                       and k[11] is not False}
    bare_parts_vac = {k[1][3] for k in produced if not k[1][4] and k[8]}
    # ... and the OPERAND leg on its own: a probe whose condition restricts
    # something but whose operand resolution came back with something NOT usable
    # as it stands must show parts_usable False, which is exactly the branch the
    # unconditional claim got wrong.
    bare_parts_op = {k[1][3] for k in produced
                     if not k[1][4] and not k[8] and not k[10]}
    if bare_parts_op != {False}:
        problems.append("bare-return parts_usable on probes whose operand "
                        "resolution came back NOT usable as it stands=%r "
                        "(want {False}) " % (sorted(bare_parts_op),))
    op_seen = {k[10] for k in covered}
    if op_seen != {True, False}:
        problems.append("operand_resolution_usable realized=%r (want both)"
                        % (sorted(op_seen),))
    # ... and the CONDITION leg on its own: a probe whose operand resolves usably
    # and whose condition restricts something, but whose delegated condition
    # resolution came back with something NOT usable as it stands, must show
    # parts_usable False -- exactly the branch the two-part claim got wrong.
    bare_parts_cond = {k[1][3] for k in produced
                       if not k[1][4] and not k[8] and k[10] and k[11] is False}
    if bare_parts_cond != {False}:
        problems.append("bare-return parts_usable on probes whose CONDITION "
                        "resolution came back NOT usable as it stands=%r "
                        "(want {False}) " % (sorted(bare_parts_cond),))
    cond_seen = {k[11] for k in covered if k[11] is not None}
    if cond_seen != {True, False}:
        problems.append("condition_resolution_usable realized=%r (want both)"
                        % (sorted(cond_seen),))
    if bare_parts_real != {True} or bare_parts_vac != {False}:
        problems.append("bare-return parts_usable: condition-restricts-something"
                        "=%r (want {True}), condition-restricts-nothing=%r "
                        "(want {False})"
                        % (sorted(bare_parts_real), sorted(bare_parts_vac)))
    # BOTH ARMS of the resolving step this resolution hands off to, and both
    # usability outcomes of a distinct yield. The resolving step is a different
    # callee that decides for itself (aggregates.py:66), so a space realizing only
    # the distinct-and-usable arm would leave the other arms unchecked -- which is
    # exactly the coverage hole these families close.
    yield_arms = {k[9] for k in covered if k[9] is not None}
    want_arms = {(True, True), (True, False), (False, True), (False, False)}
    if yield_arms != want_arms:
        problems.append("resolving-step yields (distinct, yield_usable)=%r "
                        "(want %r: a distinct yield usable and not, and a step "
                        "handing back the very value it was given, that value "
                        "usable and not)"
                        % (sorted(map(str, yield_arms)),
                           sorted(map(str, want_arms))))
    # Both values of the vacuity input must be realized at all.
    vac_seen = {k[8] for k in covered}
    if vac_seen != {True, False}:
        problems.append("vacuous_condition realized=%r (want both)"
                        % (sorted(vac_seen),))
    # ... and its two halves must come APART: a condition LEFT AS WRITTEN that is
    # already usable as it stands. Where the space realizes being left as written
    # only on conditions that are also uncompilable, vacuity and unusability
    # coincide and a falsiness-only reading of the input is indistinguishable
    # from the faithful one -- the coverage hole the `emptyWhereNode` realization
    # closes, and the one this assertion keeps closed.
    left_as_written_usable = {k[12] for k in covered}
    if True not in left_as_written_usable:
        problems.append("no realization of a condition LEFT AS WRITTEN that is "
                        "usable as it stands (a childless WhereNode): being left "
                        "as written would be realized only where it coincides "
                        "with being uncompilable, so a falsiness-only reading of "
                        "vacuous_condition would go unrefuted")
    # The PROVENANCE leg must be realized on a written default whose class
    # implements no structural equality (the Subquery family), not only on the
    # `Expression` subclasses that carry it. Where it is not, a recognizer that
    # tests provenance by comparing against a re-resolution agrees with one that
    # reads the delegated call's own outcome on every input in the space, and the
    # difference between them -- which is the difference between observing the
    # real callee and observing an accident of the class hierarchy -- goes
    # unmeasured.
    provenance_no_eq = {k[13] for k in covered}
    if True not in provenance_no_eq:
        problems.append("no expression-valued default whose class implements no "
                        "structural equality (Subquery/Exists) on the arm where "
                        "resolving it yields a DISTINCT value: the provenance of "
                        "a supplied value would be probed only where equality "
                        "against a re-resolution happens to work, so a "
                        "recognizer resting on that would go unrefuted")
    # (supplied-value facts) both the pass-through and the resolved shapes.
    # Tuple shape: (a fallback VALUE is supplied, it IS the very value that was
    # written, it can be used as it stands, it is the resolved form OF the
    # written one).
    want_fb = {(False, None, None, None),          # no fallback requested
               (True, True, True, False),          # AS WRITTEN, usable as it is
                                                   # -- reached BOTH by a value
                                                   # that is not an expression
                                                   # and by one whose resolving
                                                   # step hands back the very
                                                   # value it was given (Ref)
               (True, True, False, False),         # AS WRITTEN, and NOT usable
                                                   # as it stands -- a written
                                                   # value that is not itself an
                                                   # expression can still be one
                                                   # the fallback-supplying
                                                   # expression represents as a
                                                   # FIELD REFERENCE, which no
                                                   # clause may assume away;
                                                   # also reached by a resolving
                                                   # step that hands back the
                                                   # very value it was given
                                                   # when that value is not
                                                   # usable (MultiColSource)
               (True, False, True, True),          # a DISTINCT value came back
                                                   # from resolving, usable
               (True, False, False, True)}         # a DISTINCT value came back
                                                   # from resolving that is NOT
                                                   # usable as it stands -- what
                                                   # the resolving step yields is
                                                   # not this resolution's to
                                                   # guarantee (a nested OuterRef
                                                   # hands back a bare OuterRef)
    if fb_facts != want_fb:
        problems.append("supplied-value facts=%r (want %r)"
                        % (sorted(map(str, fb_facts)), sorted(map(str, want_fb))))
    if not {(False, True), (False, False), (True, True),
            (True, False)} <= expr_usables:
        problems.append("(is_expression, usable) pairs=%r" % (sorted(expr_usables),))
    # A part that does not resolve, with and without an aggregating operand,
    # AND the nested-aggregate rejection, where every part does resolve.
    if not {(False, False), (False, True), (True, True)} <= refuse_causes:
        problems.append("rejection causes (parts_resolve, aggregating_operand)"
                        "=%r" % (sorted(refuse_causes),))
    if mixed != {("produced", False), ("refused", None)}:
        problems.append("mixed-type asymmetry=%r (want a mixed-type aggregate "
                        "PRODUCED bare and REJECTED with a fallback)"
                        % (sorted(map(str, mixed)),))
    if problems:
        print("COVERAGE FAILURE: %s; the differential did not exercise every "
              "branch of the impl region." % "; ".join(problems))
        print("status=fail")
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py's "
          "resolve_aggregation agrees with the REAL patched "
          "Aggregate.resolve_expression (django/db/models/aggregates.py:50) on "
          "%d inputs (%d exhaustive over the concrete realization space + %d "
          "seeded fuzz, seed=%d); both outcome classes, all three rejection "
          "causes, both fallback_is_expression values, both usability values "
          "of a written fallback on BOTH sides of that flag, and all three "
          "supplied-value shapes "
          "(pass-through and resolved) covered; the mixed-type aggregate is "
          "produced bare and rejected with a fallback; the fallback wrapper is "
          "born unmarked and the written default is left as it was on every "
          "fallback probe; the aggregation the wrapper supplies a fallback for "
          "has its parts in resolved form on every probe whose condition was "
          "put through resolution or was left as written already usable as it "
          "stands, and NOT on any probe whose condition was left as written and "
          "cannot be used as it stands (both sides realized, and their two "
          "halves realized apart, on the bare path too), while the "
          "returned expression's own parts are usable on one side of the "
          "usability flag and not on the other; the provenance of a supplied "
          "value is read from the delegated call itself, and is realized on "
          "written defaults whose class implements no structural equality (the "
          "Subquery family) as well as on those that do; 0 disagreements."
          % (checked, n_enumerated, checked - n_enumerated, SEED))
    print(json.dumps({
        "checked": checked,
        "enumerated": n_enumerated,
        "fuzzed": checked - n_enumerated,
        "disagreements": 0,
        "seed": SEED,
        "oracle": "called: Aggregate.resolve_expression "
                  "(django/db/models/aggregates.py:50, gold-patched)",
        "shadow": "direct (contract-stripped impl region of model.py)",
        "status": "pass",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
