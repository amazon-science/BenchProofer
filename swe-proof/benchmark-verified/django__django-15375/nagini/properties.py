# properties.py — PBT falsification battery for django__django-15375.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of resolve_aggregation for a
# new body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures / the Expression class / the FallbackValue class / the
# ResolutionRefused class) byte-identical. spec_view elides the entire impl
# region, so same_spec is GUARANTEED for every case regardless of the body.
#
# DEFENDED SURFACE (read from model.py / refinement.md / mapping.md / meta.json /
# instance.json):
#   resolve_aggregation(requested_final, fallback, fallback_is_expression,
#                       resolution_yields_distinct, resolution_yield,
#                       aggregating_operand, operand_resolution_usable,
#                       condition_resolution_usable, vacuous_condition,
#                       parts_resolve) -> Expression
#   either produces a freshly built Expression carrying SIX observed fields, or
#   REJECTS the aggregation by raising ResolutionRefused (no expression at all).
#   `fallback` is the fallback VALUE the resolved aggregation carries (a
#   FallbackValue, or None when none was requested), and it is carried through to
#   the produced expression by IDENTITY, not described by a flag. The
#   postcondition is load-bearing in four groups, all grounded directly in the
#   args (no @Pure oracle, no Result()-keyed answer-key):
#
#     RETURN-VALUE OBSERVABLES of the expression that is produced
#       (P1) Result().supplies_fallback    == (fallback is not None)
#       (P2) Result().is_final_aggregation == requested_final     # the added step
#       (P3) not Result().holds_own_fallback
#
#     THE SUPPLIED FALLBACK VALUE — pinned by OBJECT IDENTITY on both sides of
#     the resolution branch, so "the supplied fallback is the resolved one"
#     cannot be self-reported by the expression that supplies it:
#       (P4) (Result().fallback is not None) == (fallback is not None)
#       (P5) not fallback_is_expression =>
#              Result().fallback IS fallback,
#              Result().parts_usable == fallback.usable,
#              and the written value is untouched
#              (fallback.usable == Old(fallback.usable),
#               fallback.resolution_of is Old(fallback.resolution_of))
#            (the value is supplied AS WRITTEN; nothing is derived from it, and
#             passing a value through does NOT make it usable — the expression
#             built over it inherits that)
#       (P6) fallback_is_expression =>
#              Result().fallback IS resolution_yield -- the value the resolving
#              step this resolution hands off to actually handed back is what
#              gets supplied, pinned by identity -- and the written value is
#              untouched (fallback.usable == Old(fallback.usable),
#               fallback.resolution_of is Old(fallback.resolution_of)).
#              What that step YIELDS is not this resolution's to guarantee, so
#              the yield's usability is NOT claimed; it is supplied as it came
#              back.
#       (P6a) fallback_is_expression and resolution_yields_distinct =>
#              Result().fallback IS NOT fallback,
#              Result().fallback.resolution_of IS fallback,
#              Result().parts_usable == Result().fallback.usable
#            (a DISTINCT value came back: it carries the provenance edge, and the
#             expression built over it is usable exactly when it is)
#       (P6b) fallback_is_expression and not resolution_yields_distinct =>
#              Result().fallback IS fallback,
#              Result().parts_usable == fallback.usable
#            (the step handed back the very value it was given -- a value already
#             in resolved form is its own resolved form -- so that value is
#             supplied as it arrived, by the same rule as (P5))
#
#     REACHABLE-SUBSTRUCTURE OBSERVABLES — the aggregation whose fallback the
#     returned expression supplies stays reachable from it, and is left as
#     resolution made it:
#       (P7) (Result().wrapped is not None) == (fallback is not None)
#       (P8) wrapped.is_final_aggregation == requested_final, and wrapped
#            supplies no fallback, holds no fallback of its own, supplies no
#            fallback value and has no further wrapped aggregation
#       (P12) wrapped.parts_usable == (operand_resolution_usable and
#            condition_resolution_usable and not vacuous_condition) — the reachable
#            aggregation is the one resolution
#            actually RESOLVED, not some other aggregation carrying the same
#            final-flag: its operand has been PUT THROUGH resolution, and so has
#            the condition restricting it WHENEVER that condition restricts
#            anything. A condition that is present but restricts NOTHING is left
#            as written, and counts against usability only when that written form
#            cannot be used as it stands; and putting the operand through
#            resolution, or a condition
#            that does restrict something, are handed-off
#            steps whose outcome is READ, so either may come back with a form that
#            still cannot be used as it stands. Any of the three leaves the
#            aggregation not
#            usable as it stands. The equality is TWO-SIDED, which is what makes it
#            bite in both directions: an aggregation that was merely BUILT has NO
#            part resolved and fails it wherever usable parts are demanded, and an
#            aggregation whose unresolved part is claimed resolved fails it too.
#            Paired with (P5)/(P6)'s Result().parts_usable for the returned
#            expression and with Implies(fallback is None, Result().parts_usable
#            == (operand_resolution_usable and condition_resolution_usable and not
#            vacuous_condition)) for the bare
#            return, so the claim covers every path.
#
#     DOMAIN / OUTCOME-CLASS OBSERVABLES — resolution must ANSWER on every input,
#     and it rejects on EXACTLY two kinds of input:
#       (P9)  a normal return implies parts_resolve
#       (P10) a normal return implies (requested_final or not aggregating_operand)
#       (P11) Exsures(ResolutionRefused, (not parts_resolve or
#                     (aggregating_operand and not requested_final)) and the
#                     written fallback value is untouched)
#     (P9)/(P10) forbid returning an expression where the real callee has none;
#     (P11) forbids rejecting where the real callee returns one. Together they pin
#     the outcome class on the WHOLE domain — nothing is excluded by a
#     precondition. The ONE Requires clause that is not the termination level is
#     the permission to read and write the passed fallback value's own two
#     fields — ownership, not a domain restriction, and both the postcondition
#     and the Exsures hand it back with the value unchanged. NOTHING is assumed
#     about the written value: it is admitted usable or not-usable as it stands,
#     and the resolved form of anything or of nothing, INDEPENDENTLY of whether
#     it is itself an expression (refinement.md §B3 records the precondition
#     that was DELETED after the G-CONF differential refuted it on the
#     realizable input `Sum('num', default='')`).
#
#   plus the field-accessibility Ensures(Acc(Result().<field>)) for all six
#   fields and, under Implies, for the reachable aggregation's six fields and
#   for the supplied fallback value's two fields (full ownership of FRESH
#   objects, and returned ownership of the written value).
#
#   Repo binding (mapping.md): requested_final <-> the `summarize` flag;
#   `fallback is not None` <-> "the aggregation AS RESOLVED carries a fallback
#   value" (`(default := c.default) is None` at aggregates.py:63, read off the
#   resolved copy, which is what the real code reads); `fallback` itself <-> that
#   `default` OBJECT; fallback_is_expression <-> `hasattr(default,
#   'resolve_expression')` (aggregates.py:65); fallback.usable <-> that value can
#   stand as the fallback source without further resolution (it compiles: it has
#   an `as_sql`, or it is a plain value Coalesce wraps in a `Value`);
#   fallback.resolution_of <-> "this value is what resolving THAT value against
#   the query produced" (`default = default.resolve_expression(...)`,
#   aggregates.py:66); resolution_yields_distinct / resolution_yield <-> WHAT
#   THAT CALL RETURNED — a different callee, dispatched per expression class, so
#   its outcome is read rather than assumed: most classes build a new object
#   (`c = self.copy()`, expressions.py:246), while a value already in resolved
#   form hands back the very object it was given (`return self` — Ref,
#   expressions.py:902-905; MultiColSource, fields/related_lookups.py:25-26), and
#   an OuterRef over a nested OuterRef hands back its inner name, a bare OuterRef
#   with no `as_sql` (expressions.py:645-648), so the yield need not be usable
#   as it stands either; aggregating_operand <-> the aggregation aggregates over an
#   operand that itself contains an aggregate (aggregates.py:55-62);
#   parts_resolve <-> every part resolution must resolve does resolve against the
#   query (the operand, the restricting condition at aggregates.py:53, an
#   expression-valued fallback at aggregates.py:66, and — only on the fallback
#   path — the output type the fallback-supplying expression is built with,
#   `output_field=c._output_field_or_none` at aggregates.py:68, which re-raises
#   FieldError at expressions.py:280-282). is_final_aggregation <-> `is_summary`;
#   supplies_fallback <-> "the returned object IS the fallback Coalesce wrapper
#   (vs the bare aggregate)"; holds_own_fallback <-> the object still carries a
#   `default` of its own that nothing supplies yet; Result().fallback <-> the
#   wrapper's SECOND source expression (the value it supplies); wrapped <-> the
#   wrapper's FIRST source expression, i.e. the aggregation the fallback is
#   supplied FOR. ResolutionRefused <-> "no expression is produced for this
#   aggregation at all". vacuous_condition <-> the aggregation carries a
#   restricting condition that was LEFT AS WRITTEN and that written form has NO
#   `as_sql`. Left as written means it restricts NOTHING: e.g. a `Q` that is
#   present but has no
#   children, which `django/utils/tree.py:60-62` (`Node.__bool__` returns
#   `bool(self.children)`) makes FALSY, so the `and` at aggregates.py:53
#   short-circuits and the condition is never replaced by a resolved one. BOTH
#   halves matter, because falsiness alone does not decide usability: a bare
#   `WhereNode()` is equally childless and FALSY, so `:53` short-circuits on it
#   too, yet `WhereNode` DOES define `as_sql` (`django/db/models/sql/where.py:65`)
#   and the aggregation is therefore usable as it stands. So this flag is
#   "left as written AND not compilable as written", which `Q()` satisfies (no
#   `as_sql`) and `WhereNode()` does not. This is
#   unchanged base behaviour, not part of the added step, and it is realizable
#   from user-facing ORM code (`Sum('num', filter=Q())`, and Q() is the ordinary
#   accumulator seed of filter-building code; `filter=` is not restricted to `Q`
#   — `aggregates.py:32` merely stores it — so the `WhereNode()` spelling is
#   in-domain too). parts_usable <-> every part the
#   object is built from can be used as it stands: each of its source expressions,
#   and (for an aggregation) the condition restricting it, has an `as_sql`. For the
#   resolved aggregation that is established by `super().resolve_expression` — which
#   resolves the OPERANDS only (`Func.resolve_expression` walks
#   `c.source_expressions` directly, expressions.py:694-699) — followed by
#   `c.filter = c.filter and c.filter.resolve_expression(...)` for the CONDITION
#   on the very next line (aggregates.py:53). The operand resolution ALONE leaves
#   the condition a raw `Q` with no `as_sql` (G-AX fact (7)'s negative control),
#   which is why an aggregation that merely carries the right `is_summary` is not
#   necessarily the aggregation resolution produced.
#   operand_resolution_usable <-> what putting the OPERAND through resolution came
#   back with: whether that resolved form has an `as_sql`. `Func.resolve_expression`
#   (expressions.py:694-699) delegates per operand to `arg.resolve_expression`,
#   which each operand class decides for itself, so the outcome is READ here for the
#   same reason `resolution_yields_distinct` / `resolution_yield` are on the
#   fallback-value side. It is usually `True` (an `F` becomes a `Col`, a `Value`
#   stays a `Value`), but a step can succeed without rejecting and still come back
#   with something that has no `as_sql`: `OuterRef.resolve_expression` returns its
#   inner name unchanged when that name is itself an `OuterRef` (expressions.py
#   :645-648), so the aggregation carries a bare `OuterRef` and cannot be compiled.
#   Realizable from user-facing ORM code (a doubly-nested subquery aggregating over
#   `OuterRef(OuterRef('num'))`), and DISJOINT from parts_resolve, which tracks only
#   whether a resolution raised.
#   condition_resolution_usable <-> the SAME fact for the CONDITION: what putting a
#   condition that restricts something through resolution came back with, i.e.
#   whether that resolved form has an `as_sql`. `aggregates.py:53` is
#   `c.filter = c.filter and c.filter.resolve_expression(...)` — a call into a
#   DIFFERENT callee dispatched on the written condition's own class, so like the
#   operand leg its outcome is READ, not decided. Usually `True` (a `Q` becomes a
#   `WhereNode`, an `Exists` stays an `Exists`, an `F` becomes a `Col`), but a
#   condition can be put through resolution without raising and still come back
#   uncompilable: `OuterRef.resolve_expression` returns its inner name unchanged
#   when that name is itself an `OuterRef` (expressions.py:645-648), and
#   `MultiColSource.resolve_expression` is `return self` (fields/related_lookups.py
#   :25-26) — neither has an `as_sql`. Where NO such step runs (no condition, or a
#   condition restricting nothing, which short-circuits `:53`'s `and`) there is no
#   outcome of it to hold against the aggregation, so the flag is immaterial there
#   and nothing reads it. Also DISJOINT from parts_resolve.
#
#   The F2P `test_aggregation_default_after_annotation` exercises the cell
#   requested_final=True, fallback=<the int 0>, fallback_is_expression=False (a
#   final Sum with default=0 after an annotate): the wrapper MUST carry
#   is_final_aggregation=True (P2) so the query-splitter promotes it to the outer
#   query; without the added step it stays False, the wrapper is stranded in the
#   inner subquery, and the backend emits the malformed `SELECT FROM (subquery)`.
#   The P2P `test_aggregation_default_not_in_aggregate` exercises
#   requested_final=False with a fallback (a non-final inner): the wrapper MUST
#   carry is_final_aggregation=False (P2 again) — so a hard-coded True is ALSO
#   wrong (this is precisely the bogus hints_text patch `coalesce.is_summary =
#   True`, see attack `weak-hardcode-true`). The P2P
#   `test_aggregation_default_passed_another_aggregate` exercises
#   fallback_is_expression=True (`default=Avg('pages') / 10.0`) and is what
#   (P6) defends: the value the wrapper supplies must BE the resolved form of the
#   written expression, not the written expression and not anything else.
#
#   (P7)/(P8) defend the DOWNSTREAM reader: the aggregation is not dead after the
#   wrap — it is the wrapper's first source expression, and sql/query.py's
#   rewrite_cols reads its `is_summary` (`expr.contains_aggregate and not
#   expr.is_summary`) to decide whether the inner aggregate is re-selected under
#   a `__colN` alias. A reachable-substructure mutation therefore changes real
#   query construction, which is what `weak-clobber-wrapped-flag` does.
#   (P5)/(P6) defend the fallback-resolution step, which is NOT a no-op and — the
#   point of the identity pinning — is NOT self-reportable: an expression-valued
#   default must be resolved against the query before it can compile to SQL, and
#   the object the wrapper is built over must be THAT resolution
#   (`weak-drop-fallback-resolution`, `weak-unresolved-fallback-marker`,
#   `weak-echo-written-usability`, `weak-self-resolution-cycle`,
#   `weak-resolve-in-place`), while a value with nothing left to resolve must be
#   passed through untouched (`weak-resolve-always`). (P3)/(P8) defend the reset
#   of the aggregation's own fallback before wrapping, without which the inner
#   aggregate supplies the fallback a SECOND time
#   (`weak-strand-wrapped-fallback`). (P9)-(P11) defend the outcome class in both
#   directions: `weak-return-instead-of-refuse` produces an expression for an
#   aggregation whose parts do not resolve, and `weak-over-refuse-final-nested`
#   rejects an aggregate-over-aggregate even for a FINAL resolution, which the
#   P2P `test_aggregate_over_aggregate` /
#   `test_annotated_aggregate_over_annotated_aggregate` require to succeed.
#   (P12) defends the aggregation the fallback is supplied FOR being the one
#   resolution actually produced. Every flag-shaped clause above is satisfied by
#   an impl that builds a SECOND, unresolved aggregation carrying the right
#   `is_summary` and hands the `Coalesce` that instead — in the repo, a bare
#   second `super().resolve_expression(...)`, whose `filter` is never resolved
#   because `Func.resolve_expression` (expressions.py:694-699) walks only
#   `c.source_expressions` and the condition is resolved one line further on
#   (aggregates.py:53). Every test that FAILS under that rival carries a
#   `filter=`: the P2P `test_aggregation_default_passed_another_aggregate`
#   (`Sum('price', filter=Q(rating__lt=3.0), default=Avg('pages') / 10.0)`,
#   tests/aggregation/tests.py:1627) plus the filtered datetime/time default
#   cases, which crash on an unresolved `Q` at compile time. That family is
#   `weak-fresh-inner-aggregation`, `weak-fresh-inner-when-expression`,
#   `weak-fresh-bare-return`, `weak-never-resolve-parts` and
#   `weak-overclaim-wrapper-parts`; `pos-control-second-full-resolution` is the
#   calibration on the other side — wrapping a second FULLY resolved aggregation
#   (operand AND condition) is admitted, because that behaviour does resolve.
#
# READ-ONLY INPUTS -> FRAME-MUTATION IS COVERED (not N/A any more):
#   five inputs are plain immutable `bool` flags passed BY VALUE, but `fallback`
#   and `resolution_yield` are OBJECTS the callee holds full permission on, so the
#   frame-mutation probe DOES apply and is instantiated twice:
#   `weak-resolve-in-place` overwrites the written value's own `usable` field to
#   make it pass for the value that came back (rejected: (P6b)/(P6a) pin WHICH
#   object is supplied and every arm requires `fallback.usable ==
#   Old(fallback.usable)`), and `weak-resolve-always` replaces a written value
#   that needed no resolution with a derived one (rejected by (P5)'s identity
#   clause). There is no way to satisfy the
#   postcondition by writing over the input, which is exactly what the identity
#   pinning buys over a self-reported flag.
#
# UNGROUNDED-ORACLE ECHO -> N/A (grounded oracle; honest positive controls added):
#   the pure region is EMPTY (no @Pure spec helper) and every postcondition clause
#   pins Result()'s (or the reachable aggregation's, or the supplied value's)
#   fields DIRECTLY to the input args (`fallback`, `resolution_yield`,
#   requested_final, fallback_is_expression, resolution_yields_distinct), not to
#   any opaque answer-key or exact-marker the impl
#   could echo without doing the work. The one echo an identity-pinned observable
#   still admits — reporting the WRITTEN value's usability instead of producing a
#   usable resolved one — is instantiated as `weak-echo-written-usability` and is
#   rejected. Per directive 2 we also stand HONEST cheapest-impl positive controls
#   in place of the ungrounded echo (pos-control-*).
#
# CONTROL-FLOW-EFFECT -> covered by the object-identity, reachable-substructure and
#   outcome-class attacks, not a separate capability token. The value abstraction
#   has a dedicated field for each effect the real callee has: supplies_fallback
#   makes "returned the bare aggregate c vs a distinct fallback-supplying wrapper"
#   visible (`weak-return-bare-aggregate`); wrapped makes a mutation of the still
#   reachable aggregation visible (`weak-clobber-wrapped-flag`); holds_own_fallback
#   makes the reset-before-wrapping visible (`weak-strand-wrapped-fallback`);
#   fallback makes the resolution step's RESULT visible by identity rather than by
#   self-report; and the ResolutionRefused Exsures makes the raise/return outcome
#   class visible in both directions (`weak-return-instead-of-refuse`,
#   `weak-over-refuse-final-nested`). So no separate capability token is needed.
#
# AXIOMS: meta.axioms == [], the axioms region is an empty singleton, and the
#   proof consumes NO @ContractOnly callee. The only callee-level obligation is
#   the A-reference deep model of the resolution effect (the unchanged
#   super().resolve_expression stamps c.is_summary == summarize; a default yields
#   a DISTINCT Coalesce wrapper; a fresh Coalesce defaults to is_summary == False;
#   an expression-valued default resolves to a DISTINCT, compilable object while
#   the written one stays as it was) — already host-validated by axiom_check.py /
#   G-AX. We re-run that exact oracle IN-CONTAINER against the REAL Django classes
#   as the single axiom-lane probe (it imports django, builds real
#   Sum/Avg/Min/Max/Count aggregates with/without a default, and CALLS the real
#   Aggregate.resolve_expression — it does NOT regex source). It asserts ONLY
#   unchanged-callee facts present in the BASE-COMMIT image (apply_gold=False); it
#   does NOT assert the wrapper's own is_summary, which is the added step and
#   absent from the base image.
from pathlib import Path

INSTANCE = "django__django-15375"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of resolve_aggregation (verbatim from model.py). Each variant re-emits the
# `# impl-start` marker first and `# impl-end` last so the region boundary is
# preserved exactly; spec_view elides everything between them, guaranteeing
# same_spec for every variant.
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace resolve_aggregation's whole impl block with a new body.
    `body_lines` is the source BETWEEN the markers (no markers); we wrap it back
    in the exact `# impl-start` / `# impl-end` markers so the region is intact."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The head every variant shares: the two rejection checks and the construction
# of the resolved aggregation. Spelled out once so each attack below differs
# from the gold decision in exactly ONE place and the verdict is attributable.
_HEAD = (
    "    if not parts_resolve:\n"
    "        raise ResolutionRefused()\n"
    "    c = Expression(requested_final, False)\n"
    "    c.parts_usable = (operand_resolution_usable and condition_resolution_usable\n"
    "                      and not vacuous_condition)\n"
    "    c.holds_own_fallback = fallback is not None\n"
    "    if aggregating_operand and not requested_final:\n"
    "        raise ResolutionRefused()\n"
)

# The gold resolution step: an expression-valued fallback is replaced by a
# DISTINCT resolved value that records which value it is the resolution of.
_RESOLVE = (
    "    supplied = fallback\n"
    "    if fallback_is_expression:\n"
    "        if resolution_yields_distinct:\n"
    "            resolution_yield.resolution_of = fallback\n"
    "            supplied = resolution_yield\n"
    "        else:\n"
    "            supplied = fallback\n"
)

# The gold wrapping tail (the `Assert` proof aid is a Nagini-only line and is
# omitted from these bodies, which changes nothing observable).
_WRAP = (
    "    wrapper = Expression(False, True)\n"
    "    wrapper.parts_usable = supplied.usable\n"
    "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
    "    c.holds_own_fallback = False\n"
    "    wrapper.wrapped = c\n"
    "    wrapper.fallback = supplied\n"
    "    return wrapper\n"
)

# The GOLD body verbatim (used by the admissibility self-call wrappers so the
# rejection/acceptance is attributable only to the added self-call, never to a
# changed decision).
_GOLD_BODY = (
    _HEAD +
    "    if fallback is None:\n"
    "        return c\n" +
    _RESOLVE +
    _WRAP
)


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS — structurally-different CORRECT impls that MUST verify.
    # =====================================================================

    # ------------------------------------------------------------ soundness (1)
    # POSITIVE CONTROL A (compute-then-construct). Build the wrapper's final-flag
    # into the CONSTRUCTOR directly (Expression(requested_final, True)) instead of
    # constructing unmarked then reassigning — a genuinely different executable
    # shape that produces the IDENTICAL observable object. It also drops the
    # `Assert(not wrapper.is_final_aggregation)` proof aid, which no longer holds
    # of this shape and is not part of the claim. If it cannot verify =>
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-construct-marked",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    # Different shape: stamp the requested final-flag at construction\n"
            "    # time rather than constructing unmarked then reassigning.\n"
            "    wrapper = Expression(requested_final, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "rationale": "a correct impl with a DIFFERENT executable shape (mark the "
                     "wrapper at construction, no post-hoc reassignment, no "
                     "framing Assert) must verify: it satisfies every clause "
                     "(P1)-(P11) on every input. No invariant to drop "
                     "(straight-line). Else SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------ soundness (2)
    # POSITIVE CONTROL B (read the flags through intermediate locals). Cheapest
    # honest impl that still does the real work: it computes the propagated flag
    # from c via a named local and reads the requested-fallback test through
    # another. Stands in place of the N/A ungrounded-oracle echo (directive 2):
    # the oracle is grounded in the args, so the cheapest correct impl simply
    # recomputes the per-input answer. Must verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-intermediate-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _HEAD +
            "    wants_fallback = fallback is not None\n"
            "    if not wants_fallback:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    # The propagated flag read through a named local.\n"
            "    propagated = c.is_final_aggregation\n"
            "    wrapper.is_final_aggregation = propagated\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "rationale": "grounded-oracle honest positive control: the cheapest correct "
                     "impl recomputes the propagated final-flag from c via a named "
                     "local and tests for a requested fallback through another. "
                     "Must verify; else SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------ soundness (3)
    # POSITIVE CONTROL C (both rejection checks hoisted before the aggregation is
    # built, and merged into ONE raise). The order of the two rejection checks is
    # unobservable — both produce the same outcome, "no expression at all" — so a
    # correct impl may test them in either order and in either arrangement. This
    # is the control that keeps (P9)-(P11) from over-fitting to the gold ORDER of
    # the checks. Must verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-merged-refusal",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Both rejection cases decided up front, in one test, before any\n"
            "    # expression is built: same outcome class on the same inputs.\n"
            "    if (not parts_resolve) or (aggregating_operand and not requested_final):\n"
            "        raise ResolutionRefused()\n"
            "    c = Expression(requested_final, False)\n"
            "    c.parts_usable = (operand_resolution_usable and condition_resolution_usable\n"
            "                      and not vacuous_condition)\n"
            "    c.holds_own_fallback = fallback is not None\n"
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            _WRAP
        ),
        "rationale": "the two rejection cases produce the SAME outcome (no "
                     "expression), so deciding them in one merged test before "
                     "building anything is observationally identical. Guards "
                     "(P9)-(P11) against over-fitting to the gold ORDER of the "
                     "checks. Must verify; else SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------ soundness (4)
    # POSITIVE CONTROL D (resolve the fallback AFTER the wrapper exists). The
    # recorded refutation atk_12 exploited exactly this reordering when the
    # supplied fallback was described by a FLAG on the wrapper: moving the flag
    # assignment after the wrap was observationally free. With the value pinned by
    # IDENTITY the reordering is STILL free for an HONEST impl — the resolved
    # value may be built before or after the wrapper — and this control proves the
    # repair did not simply forbid the order. Must verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-resolve-after-wrap",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    wrapper = Expression(False, True)\n"
            "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    # Different shape: the resolution of an expression-valued fallback\n"
            "    # happens AFTER the wrapper exists and is assigned straight into\n"
            "    # it. Same objects, same observables, different order.\n"
            "    if fallback_is_expression and resolution_yields_distinct:\n"
            "        resolution_yield.resolution_of = fallback\n"
            "        wrapper.fallback = resolution_yield\n"
            "        wrapper.parts_usable = resolution_yield.usable\n"
            "    else:\n"
            "        wrapper.fallback = fallback\n"
            "        wrapper.parts_usable = fallback.usable\n"
            "    return wrapper\n"
        ),
        "rationale": "the ORDER of the resolution step relative to the wrap is "
                     "unobservable for an honest impl (the same distinct resolved "
                     "value is supplied either way), and this is the exact "
                     "reordering the recorded refutation atk_12 exploited against "
                     "the flag-shaped predecessor. It must still verify: the "
                     "repair pins WHICH VALUE is supplied, not WHEN it is built. "
                     "Else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition must admit a normal F2P-shaped input, and
    # the identity-pinned postcondition must be USABLE by a caller (not a
    # contradiction that verifies vacuously).
    # =====================================================================
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": None,  # filled in below by _ADMISS_BODY
        "rationale": "placeholder replaced below; see admissibility note.",
    },
    {
        "id": "admiss-self-call-expression-fallback",
        "kind": "admissibility",
        "expect": "verify",
        "module": None,  # filled in below by _ADMISS_EXPR_BODY
        "rationale": "placeholder replaced below; see admissibility note.",
    },

    # =====================================================================
    # UNIQUENESS — same-spec WRONG impls that MUST be rejected.
    # =====================================================================

    # ----------------------------------------------------------- uniqueness (1)
    # ATTACK 1 (PARTIAL-DOMAIN / BUG-DELTA = model_prepatch). Drop the propagation
    # (refinement A6): construct the wrapper unmarked and return it WITHOUT
    # copying c's final-flag. CORRECT on every cell where requested_final is False
    # (the unmarked default already matches); WRONG exactly when a fallback is
    # requested and requested_final is True (the F2P cell). Must reject on (P2).
    {
        "id": "weak-drop-propagation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    # BUG: return the wrapper UNMARKED (drops `coalesce.is_summary =\n"
            "    # c.is_summary`), so a final aggregation's fallback wrapper keeps\n"
            "    # the class default False.\n"
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "this is model_prepatch.py / the PRE-PATCH tail: the fresh "
                      "Coalesce wrapper inherits is_summary=False and is returned "
                      "without `coalesce.is_summary = c.is_summary`. For a FINAL "
                      "aggregate with a default after an annotate() (summarize=True, "
                      "default set) the wrapper stays is_summary=False, so the "
                      "query-splitter (query.py:476) does NOT promote it to the outer "
                      "aggregate query; it is stranded in the inner subquery, the "
                      "outer query selects nothing, and the backend emits the "
                      "malformed `SELECT FROM (subquery)`. The F2P "
                      "`test_aggregation_default_after_annotation` "
                      "(Sum('double_num_awards', default=0) after an annotate) then "
                      "crashes instead of returning 40. The faithful real patch does "
                      "NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P2) Result().is_final_aggregation "
                     "== requested_final: the wrapper carries False while "
                     "requested_final is True on the fallback path, so the "
                     "equality fails. This is exactly G-DIFF (model_prepatch fails "
                     "on the same clause).",
    },

    # ----------------------------------------------------------- uniqueness (2)
    # ATTACK 2 (the BOGUS hints_text patch — hard-code True). The mailing-list
    # patch in hints_text wrote `coalesce.is_summary = True` (a constant), not
    # `= c.is_summary`. CORRECT only when requested_final is True; WRONG on a
    # NON-final aggregate with a fallback — the P2P
    # `test_aggregation_default_not_in_aggregate` cell. Must reject on (P2). This
    # is a true partial-domain rival: it passes the headline F2P but breaks an
    # existing test.
    {
        "id": "weak-hardcode-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    # BUG: hard-code the marking True (the bogus hints_text patch\n"
            "    # `coalesce.is_summary = True`) instead of copying c's flag.\n"
            "    wrapper.is_final_aggregation = True\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "this is the INCORRECT mailing-list patch quoted in hints_text "
                      "(`coalesce.is_summary = True`, a constant). It marks EVERY "
                      "fallback wrapper as a final aggregation, even when the inner "
                      "aggregate is NOT a summary. For a non-final aggregate with a "
                      "default (the P2P `test_aggregation_default_not_in_aggregate`: "
                      "annotate(avg_rating=Avg('book__rating', default=2.5)) then "
                      "aggregate(Sum('num_awards'))), the Avg-with-default annotation "
                      "is a NON-summary expression that must keep is_summary=False; "
                      "marking it True would wrongly promote it to the outer query / "
                      "change the produced SQL, so that P2P test fails. The faithful "
                      "real patch (hard-coding True) does NOT resolve the full F2P+P2P "
                      "set.",
        "rationale": "rejected by POSTCONDITION (P2): the spec pins "
                     "is_final_aggregation == requested_final UNCONDITIONALLY (both "
                     "summarize values). When requested_final is False on the "
                     "fallback path, the hard-coded True violates the equality. "
                     "This is why the spec keys on c's flag, not a constant.",
    },

    # ----------------------------------------------------------- uniqueness (3)
    # ATTACK 3 (OBJECT-IDENTITY / control-flow-effect — the historical too-weak
    # counterexample). Return the BARE aggregate c on the fallback path (drop the
    # Coalesce wrapper entirely). c already carries is_final_aggregation ==
    # requested_final, so it satisfies (P2); it is rejected by (P1) because
    # c.supplies_fallback == False != (fallback is not None) on this path, and also
    # by (P3)/(P4)/(P7). This is the rival the SECOND observable was added to kill
    # (G-EQ / refinement §B); it is also the control-flow/object-identity
    # discriminator.
    {
        "id": "weak-return-bare-aggregate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    # BUG: return the BARE aggregate on the fallback path too (no\n"
            "    # wrapper), dropping the fallback value entirely. c already carries\n"
            "    # the correct final-flag, so this would pass a final-flag-only spec.\n"
            "    return c\n"
        ),
        "refinement": "returning the bare aggregate `c` on the fallback path drops "
                      "the `Coalesce(c, default, ...)` wrapper, so the resolved "
                      "expression no longer supplies the `default` when the aggregate "
                      "is empty. EVERY `test_aggregation_default_*` test "
                      "(default_integer / default_zero / default_expression / "
                      "default_after_annotation / ...) asserts the default value is "
                      "returned on an empty/normal aggregate; without the Coalesce "
                      "they get the bare aggregate result (None on empty / no "
                      "fallback) and FAIL with `None != <default>`. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P1) Result().supplies_fallback == "
                     "(fallback is not None): on the fallback path c.supplies_fallback "
                     "is False while a fallback was requested, so the equality fails "
                     "(and (P3) fails too: c still holds its own fallback, and (P4) "
                     "fails: it supplies no fallback VALUE). This is the "
                     "object-identity/control-flow rival; the supplies_fallback "
                     "observable is exactly what discriminates it (G-EQ).",
    },

    # ----------------------------------------------------------- uniqueness (4)
    # ATTACK 4 (PARTIAL-DOMAIN, INVERTED structure). Build the wrapper on the
    # NO-fallback path and return the bare aggregate on the fallback path — i.e.
    # swap which path wraps. WRONG on (P1) on both paths (it inverts supplies_
    # fallback w.r.t. whether a fallback was requested). A catastrophic structural
    # inversion; cheap supporting near-miss but carries a real refinement.
    {
        "id": "weak-inverted-wrap-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is not None:\n"
            "        # BUG: on the fallback path return the BARE aggregate...\n"
            "        return c\n"
            "    # ...and on the NO-fallback path fabricate a fallback wrapper.\n"
            "    wrapper = Expression(requested_final, True)\n"
            "    wrapper.parts_usable = True\n"
            "    wrapper.wrapped = c\n"
            "    return wrapper\n"
        ),
        "refinement": "this inverts the wrapping decision: it returns the bare "
                      "aggregate when a default WAS supplied (dropping the Coalesce, "
                      "so the default is lost) and fabricates a fallback-supplying "
                      "Coalesce when NO default was supplied (wrapping an aggregate "
                      "that should be returned bare, changing the emitted SQL). Both "
                      "the F2P (default lost) and the no-default P2P aggregate tests "
                      "(spurious Coalesce) FAIL. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "rejected by POSTCONDITION (P1): supplies_fallback is set "
                     "opposite to whether a fallback was requested on both paths, so "
                     "Result().supplies_fallback == (fallback is not None) fails on "
                     "every input. Supporting near-miss with a real refinement "
                     "(structural inversion).",
    },

    # ----------------------------------------------------------- uniqueness (5)
    # ATTACK 5 (PARTIAL-DOMAIN, NEGATED final-flag). Keep the correct wrapper
    # structure (P1 holds) but propagate the NEGATION of c's final-flag onto the
    # wrapper. Rejected on (P2). Distinct from attack 1 (drop) and attack 2
    # (constant True): here the flag DEPENDS on the input but with the wrong sign,
    # which a "uses requested_final somewhere" heuristic would miss.
    {
        "id": "weak-negated-final-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    # BUG: propagate the NEGATION of the aggregate's final-flag.\n"
            "    wrapper.is_final_aggregation = not c.is_final_aggregation\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "this stamps the wrapper with `not c.is_summary`. For a final "
                      "aggregate with a default after an annotate (the F2P, "
                      "summarize=True) the wrapper gets is_summary=False — the SAME "
                      "stranding as the unpatched code, so the F2P still crashes with "
                      "`SELECT FROM (subquery)`. (And for a non-final aggregate it "
                      "wrongly marks the wrapper True.) The faithful real patch "
                      "(negated propagation) does NOT resolve the F2P.",
        "rationale": "rejected by POSTCONDITION (P2): Result().is_final_aggregation "
                     "== not requested_final, which differs from the required "
                     "requested_final whenever requested_final is True on the "
                     "fallback path. The equality fails on the F2P cell.",
    },

    # ----------------------------------------------------------- uniqueness (6)
    # ATTACK 6 (REACHABLE-SUBSTRUCTURE / control-flow-effect). Do the propagation
    # correctly, then CLOBBER the aggregation the wrapper supplies the fallback
    # for. The returned object is observationally perfect; the damage is one edge
    # away. Rejected by (P8). This is the rival the `wrapped` edge was added to
    # kill: the aggregation is NOT dead after the wrap.
    {
        "id": "weak-clobber-wrapped-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            _WRAP.replace(
                "    return wrapper\n",
                "    # BUG: overwrite the final-flag of the aggregation the wrapper\n"
                "    # supplies the fallback for. The RETURNED object is untouched, so\n"
                "    # a spec that observed only the return value could not see this.\n"
                "    c.is_final_aggregation = not requested_final\n"
                "    return wrapper\n")
        ),
        "refinement": "the aggregate is NOT dead after the wrap: it is the Coalesce's "
                      "FIRST SOURCE EXPRESSION and stays reachable from the returned "
                      "wrapper. Its `is_summary` is read downstream by "
                      "sql/query.py's rewrite_cols (`expr.contains_aggregate and not "
                      "expr.is_summary`), which decides whether the inner aggregate is "
                      "re-selected under a `__colN` alias. `coalesce.is_summary = "
                      "c.is_summary; c.is_summary = not summarize` therefore keeps the "
                      "wrapper right and corrupts the source expression: the F2P "
                      "`test_aggregation_default_after_annotation` FAILS (measured "
                      "0/1) while every P2P still passes. The faithful real patch does "
                      "NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P8) Result().wrapped."
                     "is_final_aggregation == requested_final: the clobber sets it to "
                     "the negation on the fallback path. (P7) makes the "
                     "aggregation reachable from the return value at all, which is "
                     "what gives (P8) something to constrain.",
    },

    # ----------------------------------------------------------- uniqueness (7)
    # ATTACK 7 (DEGENERATE BRANCH / the RECORDED REFUTATION's move). Delete the
    # fallback-resolution step entirely and supply the value exactly as written.
    # This is the shape the previous, flag-shaped spec licensed: the wrapper's
    # `fallback_resolved` boolean could be set while the resolution's RESULT was
    # discarded (recorded attack atk_12, G-EQ BROKEN). With the supplied value
    # pinned by IDENTITY there is nothing left to self-report. Rejected by (P6).
    {
        "id": "weak-drop-fallback-resolution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    # BUG: skip the fallback-resolution step — supply the fallback value\n"
            "    # exactly as written, even when it is itself an expression.\n"
            "    supplied = fallback\n" +
            _WRAP
        ),
        "refinement": "the fallback-resolution step is NOT a no-op. For an "
                      "expression-valued default (e.g. Sum('price', "
                      "default=Avg('pages') / 10.0)) `default = "
                      "default.resolve_expression(query, allow_joins, reuse, "
                      "summarize)` (aggregates.py:66) is what makes the value "
                      "compilable: an unresolved F/CombinedExpression has no `as_sql` "
                      "(expressions.py:582-597 defines F with resolve_expression and "
                      "NO as_sql), so the Coalesce cannot compile. Deleting the step "
                      "while keeping the propagation passes the F2P (measured 1/1) and "
                      "REGRESSES the P2P "
                      "`test_aggregation_default_passed_another_aggregate` (measured "
                      "94/95). The faithful real patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P6): with an expression-valued "
                      "fallback the spec demands the supplied value be a DISTINCT "
                      "object that is the resolved form OF the written one, so "
                      "supplying the written object itself cannot even be framed "
                      "(Nagini reports insufficient permission for "
                      "Acc(Result().fallback.usable) alongside Acc(fallback.usable) "
                      "— two permissions on one location — the permission-level "
                      "reading of `Result().fallback is not fallback`). This is the "
                      "clause that replaced the self-reported `fallback_resolved` "
                      "flag the recorded attack atk_12 exploited.",
    },

    # ----------------------------------------------------------- uniqueness (8)
    # ATTACK 8 (MISSING EFFECT on the reachable aggregation). Keep everything gold
    # but leave the aggregation still holding its own fallback value when it is
    # wrapped, so the fallback is supplied TWICE. Rejected by (P8).
    {
        "id": "weak-strand-wrapped-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
            "    # BUG: leave the aggregation still holding its own fallback value\n"
            "    # while wrapping it in the expression that supplies that fallback.\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "dropping `c.default = None  # Reset the default argument "
                      "before wrapping.` (aggregates.py:67) leaves the inner "
                      "aggregate carrying its own default while it sits inside the "
                      "Coalesce that already supplies that default. Aggregate.as_sql "
                      "wraps a default-carrying aggregate in a Coalesce of its own at "
                      "compile time, so the emitted SQL becomes "
                      "COALESCE(COALESCE(SUM(...), d), d) — a different query from the "
                      "one the `test_aggregation_default_*` P2P tests assert (and the "
                      "doubled wrapper changes the output_field/alias structure the "
                      "query-splitter walks). The faithful real patch does NOT "
                      "resolve.",
        "rationale": "rejected by POSTCONDITION (P8) not Result().wrapped."
                     "holds_own_fallback: the wrapped aggregation is left with "
                     "holds_own_fallback True on the fallback path. This is the "
                     "reset-before-wrapping effect made observable.",
    },

    # ----------------------------------------------------------- uniqueness (9)
    # ATTACK 9 (OUTCOME CLASS, over-refusal). Reject every aggregate-over-aggregate
    # regardless of whether a FINAL resolution was requested. This is a
    # preservation rival: it does not touch the propagation at all, it removes a
    # capability the function already had. Rejected by (P11).
    {
        "id": "weak-over-refuse-final-nested",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not parts_resolve:\n"
            "        raise ResolutionRefused()\n"
            "    c = Expression(requested_final, False)\n"
            "    c.parts_usable = (operand_resolution_usable and condition_resolution_usable\n"
            "                      and not vacuous_condition)\n"
            "    c.holds_own_fallback = fallback is not None\n"
            "    # BUG: reject an aggregation over another aggregation even when a\n"
            "    # FINAL resolution was requested, where it must still succeed.\n"
            "    if aggregating_operand:\n"
            "        raise ResolutionRefused()\n"
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            _WRAP
        ),
        "refinement": "the nested-aggregate FieldError guard is deliberately gated on "
                      "`if not summarize:` (aggregates.py:55) — a FINAL (summarize) "
                      "resolution of an aggregate over an aggregate is legal and is "
                      "exactly what `.aggregate(Sum('...'))` over an annotated "
                      "aggregate does. Dropping the `not summarize` gate makes the "
                      "guard fire on the final resolution too, so the P2P tests "
                      "`test_aggregate_over_aggregate` and "
                      "`test_annotated_aggregate_over_annotated_aggregate` raise "
                      "FieldError instead of returning their aggregates. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "rejected by the EXSURES (P11): the exceptional postcondition "
                     "permits ResolutionRefused only when `not parts_resolve or "
                     "(aggregating_operand and not requested_final)`, so raising "
                     "with aggregating_operand and requested_final both True "
                     "violates it. This is a PRESERVATION clause — it protects a "
                     "capability the function had before and after — and it is why "
                     "the domain is modelled with an outcome class rather than cut "
                     "out of the precondition.",
    },

    # --------------------------------------------------------- uniqueness (10)
    # ATTACK 10 (OUTCOME CLASS, under-refusal / swallowed failure). Produce an
    # expression even when a part the resolution must resolve does not resolve.
    # Rejected by (P9).
    {
        "id": "weak-return-instead-of-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # BUG: no rejection when a part that must be resolved cannot be —\n"
            "    # an expression is produced for the aggregation regardless.\n"
            "    c = Expression(requested_final, False)\n"
            "    c.parts_usable = (operand_resolution_usable and condition_resolution_usable\n"
            "                      and not vacuous_condition)\n"
            "    c.holds_own_fallback = fallback is not None\n"
            "    if aggregating_operand and not requested_final:\n"
            "        raise ResolutionRefused()\n"
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            _WRAP
        ),
        "refinement": "swallowing an unresolvable part (an operand naming no field, a "
                      "restricting condition that does not resolve, an "
                      "expression-valued default over a bad reference, or an "
                      "aggregate whose output type cannot be determined on the "
                      "fallback path) and returning an expression anyway means the "
                      "FieldError the aggregation tests assert never arrives: the "
                      "aggregate compiles a reference to nothing and the failure "
                      "surfaces as a database error, or silently wrong SQL, far from "
                      "the call. The aggregation P2P suite asserts the FieldError "
                      "(e.g. the nonexistent-field, mixed-types and "
                      "aggregate-over-aggregate error tests). The faithful real patch "
                      "does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P9) parts_resolve: a normal return "
                     "asserts that every part resolution needed did resolve, so "
                     "returning with parts_resolve False violates it. The paired "
                     "Exsures (P11) is what keeps this from being dodged by rejecting "
                     "everything instead.",
    },

    # --------------------------------------------------------- uniqueness (11)
    # ATTACK 11 (OVER-APPROXIMATION of the resolution branch). Resolve the
    # fallback value UNCONDITIONALLY — drop the test for whether the value is
    # itself an expression. This is a strict over-approximation: it does strictly
    # MORE work than gold, and a spec that only demanded "the supplied value is a
    # usable resolution" would license it. Rejected by (P5).
    {
        "id": "weak-resolve-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    # BUG: resolve the fallback value even when it is not itself an\n"
            "    # expression — replace it with a derived value unconditionally.\n"
            "    yielded = FallbackValue(True)\n"
            "    yielded.resolution_of = fallback\n"
            "    supplied = yielded\n" +
            _WRAP
        ),
        "refinement": "this is `default = default.resolve_expression(query, "
                      "allow_joins, reuse, summarize)` with the `hasattr(default, "
                      "'resolve_expression')` guard (aggregates.py:65) DELETED. A "
                      "plain default has no `resolve_expression` at all, so the very "
                      "F2P cell (`Sum('double_num_awards', default=0)` — the int 0) "
                      "raises AttributeError: 'int' object has no attribute "
                      "'resolve_expression' before any expression is produced. Every "
                      "plain-value default test (default_zero / default_integer / "
                      "default_decimal / ...) fails the same way. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P5): when the fallback value is NOT "
                     "itself an expression the spec demands the returned expression "
                     "supply THAT VERY OBJECT (Result().fallback is fallback), so a "
                     "derived stand-in fails the identity. This is the clause that "
                     "keeps the identity pinning two-sided — a pass-through is "
                     "required exactly where resolution is not.",
    },

    # --------------------------------------------------------- uniqueness (12)
    # ATTACK 12 (BOUNDARY TOKEN SWAP on the resolution's back-reference). Build a
    # fresh, usable value — but do not record WHICH value it is the resolution of.
    # Structurally almost gold: one token (`fallback` -> `None`). Rejected by (P6).
    {
        "id": "weak-unresolved-fallback-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    supplied = fallback\n"
            "    if fallback_is_expression:\n"
            "        # BUG: do not record which value this is the resolution of —\n"
            "        # supply the value that came back unrelated to the requested one.\n"
            "        if resolution_yields_distinct:\n"
            "            resolution_yield.resolution_of = None\n"
            "            supplied = resolution_yield\n"
            "        else:\n"
            "            supplied = fallback\n" +
            _WRAP
        ),
        "refinement": "the Coalesce's SECOND source expression must be what resolving "
                      "the WRITTEN default produced (aggregates.py:66-68). Handing it "
                      "some other resolved expression instead is a wrong fallback "
                      "VALUE: the P2P "
                      "`test_aggregation_default_passed_another_aggregate` "
                      "(Sum('price', filter=Q(rating__lt=3.0), "
                      "default=Avg('pages') / 10.0), tests/aggregation/tests.py:"
                      "1627-1631) asserts a specific number computed from that "
                      "default, so a Coalesce over a different second source returns a "
                      "different value and the test FAILS. The faithful real patch "
                      "does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P6) Result().fallback.resolution_of "
                     "is fallback: the supplied value is fresh and usable but is not "
                     "recorded as the resolved form of the requested value, so the "
                     "identity fails. Being a resolution of SOMETHING is not enough; "
                     "it must be the resolution of THIS value.",
    },

    # --------------------------------------------------------- uniqueness (13)
    # ATTACK 13 (ORACLE ECHO on the resolved value's usability). Do the resolution
    # and record the back-reference correctly, but carry the WRITTEN value's
    # usability over to the resolved one instead of producing a usable value —
    # i.e. echo an input flag where the work's RESULT is required. Rejected by
    # (P6).
    {
        "id": "weak-echo-written-usability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    supplied = fallback\n"
            "    if fallback_is_expression:\n"
            "        # BUG: supply a value derived from an input flag instead of the\n"
            "        # value the resolving step actually handed back.\n"
            "        echoed = FallbackValue(fallback.usable)\n"
            "        echoed.resolution_of = fallback\n"
            "        supplied = echoed\n" +
            _WRAP
        ),
        "refinement": "resolving an expression-valued default is what makes it "
                      "COMPILABLE: an unresolved `F('rating')` has a "
                      "resolve_expression but NO as_sql (expressions.py:582-597), "
                      "while the resolved `Col` does; a `CombinedExpression` resolves "
                      "to a distinct object whose operands are resolved "
                      "(expressions.py:492-514). Carrying the written value's "
                      "compilability over to the object handed to the Coalesce models "
                      "a resolution step that returns something still unresolved, "
                      "which crashes at SQL compile time (AttributeError: 'F' object "
                      "has no attribute 'as_sql') for the P2P "
                      "`test_aggregation_default_passed_another_aggregate`. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P6) Result().fallback.usable: the "
                     "resolved value must be usable as it stands, and the spec admits "
                     "expression-valued fallbacks that are NOT usable as written "
                     "(that is why the precondition constrains `usable` only for "
                     "non-expressions), so echoing the input flag fails on exactly "
                     "those inputs. This is the ungrounded-echo family instantiated "
                     "on the ONE observable an identity-pinned value still leaves "
                     "self-reportable.",
    },

    # --------------------------------------------------------- uniqueness (14)
    # ATTACK 14 (FRAME MUTATION / resolve IN PLACE). Mutate the WRITTEN value to
    # make it usable and supply that same object, instead of producing a distinct
    # resolved one. This is the frame-mutation probe the object-valued input makes
    # applicable: it tries to satisfy the postcondition by writing over the input.
    # Rejected by (P6).
    {
        "id": "weak-resolve-in-place",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    supplied = fallback\n"
            "    if fallback_is_expression:\n"
            "        # BUG: make the WRITTEN value usable in place and supply that\n"
            "        # very object, rather than producing a distinct resolved value.\n"
            "        fallback.usable = True\n"
            "        supplied = fallback\n" +
            _WRAP
        ),
        "refinement": "`default.resolve_expression(...)` returns a NEW object — "
                      "BaseExpression.resolve_expression starts with `c = self.copy()` "
                      "(expressions.py:246) and CombinedExpression the same "
                      "(expressions.py:513) — and the written default is NOT private "
                      "to this call: `c = super().resolve_expression(...)` is a "
                      "shallow copy, so `c.default` is the SAME object as the "
                      "user's aggregate's `default`. Resolving it in place would "
                      "write a query-bound resolved expression back into the "
                      "aggregate the user still holds, so re-resolving that same "
                      "aggregate (a queryset is resolved once per execution, and "
                      "aggregate instances are reused across querysets) would compile "
                      "a default bound to the WRONG query. The real callee leaves the "
                      "written value untouched, which axiom_check.py asserts against "
                      "the base image.",
        "rationale": "rejected by POSTCONDITION (P6): the spec demands a DISTINCT "
                     "object (Result().fallback is not fallback) AND that the written "
                     "value be left as it was (fallback.usable == "
                     "Old(fallback.usable)); supplying the input object cannot even "
                     "be framed (Nagini reports insufficient permission for "
                     "Acc(Result().fallback.usable) alongside Acc(fallback.usable)). "
                     "This is the mandatory frame-mutation probe: there is no way to "
                     "satisfy the postcondition by writing over the input.",
    },

    # --------------------------------------------------------- uniqueness (15)
    # ATTACK 15 (SELF-REFERENCE / vacuity probe on the back-reference). Record the
    # resolved value as the resolution of ITSELF — a well-typed, fresh, usable
    # value whose provenance edge points nowhere real. Rejected by (P6).
    {
        "id": "weak-self-resolution-cycle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n"
            "    supplied = fallback\n"
            "    if fallback_is_expression:\n"
            "        # BUG: point the provenance edge at the yielded value itself, so\n"
            "        # nothing records that the REQUESTED value was resolved.\n"
            "        if resolution_yields_distinct:\n"
            "            resolution_yield.resolution_of = resolution_yield\n"
            "            supplied = resolution_yield\n"
            "        else:\n"
            "            supplied = fallback\n" +
            _WRAP
        ),
        "refinement": "same real consequence as `weak-unresolved-fallback-marker` "
                      "reached by a different route: the object handed to the Coalesce "
                      "as its second source is not derived from the user's `default` "
                      "at all, so the fallback the query returns for an empty "
                      "aggregate is not the value the user asked for and the "
                      "`test_aggregation_default_*` value assertions FAIL. It is kept "
                      "as a separate case because a spec could accidentally pin only "
                      "`resolution_of is not None` (a provenance edge EXISTS) rather "
                      "than `resolution_of is fallback` (it points at the requested "
                      "value), and this is the rival that distinguishes those two.",
        "rationale": "rejected by POSTCONDITION (P6) Result().fallback.resolution_of "
                     "is fallback: the edge points at the fresh value, not at the "
                     "requested one. Confirms the clause is the strong form (the edge "
                     "must point AT the requested value), not the weak "
                     "'some edge exists' form.",
    },
    # ------------------------------------------------------------ soundness (5)
    # POSITIVE CONTROL E (CALIBRATION for (P12)). Resolve the aggregation a
    # SECOND time -- FULLY: operand AND condition -- and supply the fallback for
    # THAT resolution instead of the first one. This is the shape the auditor's
    # "generous" rival takes in the repo (a second
    # `super().resolve_expression(...)` FOLLOWED BY re-resolving `c.filter`), and
    # that rival RESOLVES under the official harness (measured: F2P 1/1, P2P
    # 95/95). So the spec MUST admit it: (P12) forbids wrapping an aggregation
    # whose parts were never resolved, NOT wrapping a different aggregation. If
    # this cannot verify => SPEC-TOO-STRONG (the repair would have outlawed a
    # behaviour that is correct).
    {
        "id": "pos-control-second-full-resolution",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
            "    c.holds_own_fallback = False\n"
            "    # Different shape: a SECOND, FULLY resolved aggregation (its parts\n"
            "    # resolved too) is the one whose fallback is supplied. Same\n"
            "    # observables, and this is what the resolving \'generous\' rival does.\n"
            "    c2 = Expression(requested_final, False)\n"
            "    c2.parts_usable = (operand_resolution_usable and condition_resolution_usable\n"
            "                       and not vacuous_condition)\n"
            "    c2.holds_own_fallback = False\n"
            "    wrapper.wrapped = c2\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "rationale": "CALIBRATION of the parts-usable clause (P12): wrapping a "
                     "SECOND, fully resolved aggregation is behaviourally correct "
                     "(the auditor's generous rival does exactly this and it "
                     "RESOLVES: F2P 1/1, P2P 95/95), so it must verify. (P12) "
                     "outlaws wrapping an aggregation whose PARTS were never "
                     "resolved, not wrapping a different object. Else "
                     "SPEC-TOO-STRONG.",
    },

    # --------------------------------------------------------- uniqueness (16)
    # ATTACK 16 (REACHABLE-SUBSTRUCTURE SUBSTITUTION — the G-EQ round-2 hole).
    # Supply the fallback FOR a freshly built aggregation that carries the right
    # final-flag but was never RESOLVED. Every flag-shaped clause holds of it:
    # right marking, supplies no fallback, holds no fallback of its own, no
    # further wrapped aggregation. Only (P12) sees the difference.
    {
        "id": "weak-fresh-inner-aggregation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
            "    c.holds_own_fallback = False\n"
            "    # BUG: supply the fallback FOR a fresh aggregation that carries the\n"
            "    # right final-flag but whose parts were never resolved, instead of\n"
            "    # the aggregation resolution actually produced.\n"
            "    c2 = Expression(requested_final, False)\n"
            "    c2.holds_own_fallback = False\n"
            "    wrapper.wrapped = c2\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "this is `Coalesce(super().resolve_expression(query, "
                      "allow_joins, reuse, summarize), default, ...)` — a SECOND, "
                      "BARE base resolution wrapped instead of `c`. It carries the "
                      "right `is_summary` (expressions.py:696) and fully resolved "
                      "OPERANDS, but `Func.resolve_expression` iterates "
                      "`c.source_expressions` DIRECTLY (expressions.py:694-699) and "
                      "so never touches `self.filter`; resolving the condition is the "
                      "NEXT line of Aggregate.resolve_expression (`c.filter = c.filter "
                      "and c.filter.resolve_expression(...)`, aggregates.py:53), which "
                      "this rival skips. The wrapped aggregation therefore carries a "
                      "raw `Q` with no `as_sql`. Measured with the faithful refined "
                      "patch: resolved=False — every failing test carries a `filter=`, "
                      "headed by the P2P "
                      "`test_aggregation_default_passed_another_aggregate` "
                      "(`Sum('price', filter=Q(rating__lt=3.0), "
                      "default=Avg('pages') / 10.0)`, tests/aggregation/tests.py:1627) "
                      "and the filtered datetime/time default cases. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P12) Result().wrapped.parts_usable: "
                     "the substituted aggregation was BUILT, not resolved, so nothing "
                     "establishes that the parts it is built from can be used as they "
                     "stand. This is the clause the round-2 G-EQ refutation forced: "
                     "before it, `wrapped` was only 'an Expression with the right "
                     "marking and no fallback of its own', which a fresh object "
                     "satisfies. The calibration case "
                     "`pos-control-second-full-resolution` shows the clause does not "
                     "outlaw a second FULLY resolved aggregation.",
    },

    # --------------------------------------------------------- uniqueness (17)
    # ATTACK 17 (PARTIAL-DOMAIN version of attack 16). Substitute the unresolved
    # aggregation ONLY when the fallback value is itself an expression — correct
    # on the plain-value half of the domain (the F2P cell), wrong exactly on the
    # cell the substitution breaks. A rival that passes the headline test.
    {
        "id": "weak-fresh-inner-when-expression",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    wrapper.parts_usable = supplied.usable\n"
            "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
            "    c.holds_own_fallback = False\n"
            "    # BUG (partial domain): substitute a never-resolved aggregation only\n"
            "    # when the fallback value is itself an expression; keep the real one\n"
            "    # otherwise, so the plain-value half of the domain stays correct.\n"
            "    if fallback_is_expression:\n"
            "        c3 = Expression(requested_final, False)\n"
            "        c3.holds_own_fallback = False\n"
            "        wrapper.wrapped = c3\n"
            "    else:\n"
            "        wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "the same substitution as `weak-fresh-inner-aggregation`, "
                      "gated on `hasattr(default, 'resolve_expression')` "
                      "(aggregates.py:65). The F2P "
                      "`test_aggregation_default_after_annotation` uses `default=0` (a "
                      "plain int) and still passes; the P2P "
                      "`test_aggregation_default_passed_another_aggregate` uses "
                      "`default=Avg('pages') / 10.0` WITH `filter=Q(rating__lt=3.0)` "
                      "and fails on the unresolved condition. A partial-domain rival "
                      "that keeps the headline test green: the faithful real patch does "
                      "NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P12): the clause is stated for the "
                     "whole fallback path, not only for the expression-valued half, "
                     "so gating the substitution on an input flag does not escape it. "
                     "This is the partial-domain instantiation of the round-2 hole.",
    },

    # --------------------------------------------------------- uniqueness (18)
    # ATTACK 18 (attack 16 on the NO-FALLBACK path). Return a freshly built,
    # never-resolved aggregation when no fallback was requested. The returned
    # object's flags are all correct; only "its parts are usable" is not.
    {
        "id": "weak-fresh-bare-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        # BUG: return a fresh aggregation carrying the right final-flag\n"
            "        # instead of the one resolution actually produced.\n"
            "        c4 = Expression(requested_final, False)\n"
            "        c4.holds_own_fallback = False\n"
            "        return c4\n" +
            _RESOLVE +
            _WRAP
        ),
        "refinement": "on the no-default path the real code returns `c` itself "
                      "(`return c`, aggregates.py:64) — the resolved copy. Returning a "
                      "differently built aggregation whose condition was never "
                      "resolved (`Func.resolve_expression` alone, "
                      "expressions.py:694-699, skipping aggregates.py:53) hands the "
                      "compiler a raw `Q`: every filtered aggregate WITHOUT a default "
                      "(the P2P `test_filtered_aggregates` / `test_filter_*` "
                      "aggregation cases) crashes at SQL compile time. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION Implies(fallback is None, "
                     "Result().parts_usable): a returned bare aggregation must be one "
                     "resolution RESOLVED. This is the no-fallback half of (P12), and "
                     "it is why the clause is stated on BOTH paths rather than only "
                     "under `wrapped`.",
    },

    # --------------------------------------------------------- uniqueness (19)
    # ATTACK 19 (MISSING EFFECT: never resolve the parts at all). Keep the very
    # aggregation resolution produced — but drop the step that resolves the parts
    # it is built from. Distinct from 16-18: nothing is substituted, an effect is
    # simply omitted, which is the shape a real "forgot a line" regression takes.
    {
        "id": "weak-never-resolve-parts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _swap(_HEAD,
                  "    c.parts_usable = (operand_resolution_usable and condition_resolution_usable\n"
            "                      and not vacuous_condition)\n",
                  "    # BUG: never resolve the parts the aggregation is built from —\n"
                  "    # the operand it aggregates over and the condition restricting\n"
                  "    # it are left exactly as written.\n") +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            _WRAP
        ),
        "refinement": "this drops `c = super().resolve_expression(...)`'s operand "
                      "resolution AND `c.filter = c.filter and "
                      "c.filter.resolve_expression(...)` (aggregates.py:52-53) — the "
                      "aggregation is wrapped exactly as written. Nothing in it has an "
                      "`as_sql`, so the resolved query cannot compile at all: the "
                      "whole aggregation suite fails, F2P included. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "rejected by POSTCONDITION (P12) / Implies(fallback is None, "
                     "Result().parts_usable): the aggregation the returned expression "
                     "exposes was never put into resolved form. The omission shape, "
                     "as opposed to the substitution shape of attacks 16-18.",
    },

    # --------------------------------------------------------- uniqueness (20)
    # ATTACK 20 (OVER-CLAIM on the returned expression's own parts). Assert that
    # every part of the returned expression is usable even when the value it
    # supplies is NOT — the exact freedom the (P5) `Result().parts_usable ==
    # fallback.usable` equality closes. This is the attack the repair's own new
    # observable makes possible, so it is the "exploit the freedom the repair
    # leaves" family.
    {
        "id": "weak-overclaim-wrapper-parts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _HEAD +
            "    if fallback is None:\n"
            "        return c\n" +
            _RESOLVE +
            "    wrapper = Expression(False, True)\n"
            "    # BUG: claim every part of the returned expression is usable as it\n"
            "    # stands even when the value passed straight through is not.\n"
            "    wrapper.parts_usable = True\n"
            "    wrapper.is_final_aggregation = c.is_final_aggregation\n"
            "    c.holds_own_fallback = False\n"
            "    wrapper.wrapped = c\n"
            "    wrapper.fallback = supplied\n"
            "    return wrapper\n"
        ),
        "refinement": "a `Coalesce` is only as compilable as its source "
                      "expressions: `Func.as_sql` compiles each one "
                      "(expressions.py:701-717), so a `Coalesce` over a `default` with "
                      "no `as_sql` cannot compile however well-formed the wrapper is. "
                      "A model that reports the wrapper's parts usable regardless "
                      "would license exactly the unresolved-default rival "
                      "`weak-drop-fallback-resolution` to re-enter through the new "
                      "observable, one level up: the P2P "
                      "`test_aggregation_default_passed_another_aggregate` fails the "
                      "same way. And the plain-value side is realizable, not "
                      "hypothetical: `Sum('num', default='')` becomes `F('')`, which "
                      "has no `as_sql` (expressions.py:184-189, :582-620) and is still "
                      "passed straight through.",
        "rationale": "rejected by POSTCONDITION (P5) Result().parts_usable == "
                     "fallback.usable: the equality is TWO-SIDED, so over-claiming is "
                     "as fatal as under-claiming. This is the family aimed at the "
                     "freedom the repair itself introduces — a new self-reported "
                     "boolean would have been exactly the defect the round-1 repair "
                     "removed, so the new observable is pinned to the supplied "
                     "VALUE's own usability rather than left free.",
    },
]


# ---------------------------------------------------------------------------
# Replace the two admissibility placeholders with self-calling caller bodies.
#
# (1) admiss-self-call — the F2P input cell (a final Sum with default=0 after an
# annotate) is requested_final=True, a fallback value that is NOT itself an
# expression (the int 0 has no resolve_expression) and is usable as it stands,
# aggregating_operand=False, parts_resolve=True. The caller must be able to BUILD
# such a value (FallbackValue(True)), pass it, and read back both the returned
# expression's fields and the fact that the value it supplies IS the one that was
# passed. If the call site could not be admitted for this normal input =>
# PRECOND-TOO-STRONG.
#
# (2) admiss-self-call-expression-fallback — the same for the OTHER side of the
# resolution branch, on the P2P cell `test_aggregation_default_passed_another_
# aggregate` (default=Avg('pages')/10.0, an expression that is NOT usable as
# written). This case is load-bearing for a different reason: (P6) demands
# Acc(fallback.usable) AND Acc(Result().fallback.usable) at once, which is
# satisfiable ONLY because the two are different objects. If that conjunction
# were contradictory the clause would be vacuous and every attack above would be
# rejected for the wrong reason, so this probe READS BACK all four facts
# ((P6)'s distinctness, the resolved value's usability, its back-reference, and
# the written value's preserved usability) from the caller's side. A caller that
# can consume them proves the clause is a usable claim, not a contradiction.
#
# resolve_aggregation's only value-shaped Requires are that a written value is
# the resolved form of nothing and, when it is not an expression, usable — both
# true of freshly built values — so any such call is in-domain.
#
# The level obligation imposes one PROOF duty: the self-call must descend. Both
# probes therefore sit on the no-fallback path (level 3) calling a with-fallback
# tuple (level 2), which strictly descends.
#
# Both probes ALSO exercise the outcome class: they pass parts_resolve=True and
# aggregating_operand=False, on which the Exsures condition is False, so the
# callee provably cannot reject and the call site needs no handler. That the
# no-rejection domain is non-empty and contains the F2P cell is part of the
# admissibility claim.
# ---------------------------------------------------------------------------
_ADMISS_PROBE = (
    "        # Admissibility self-call on the F2P-shaped input (final aggregate\n"
    "        # with a plain default after an annotate): requested_final=True, a\n"
    "        # fallback value that is not itself an expression and is usable as\n"
    "        # it stands, no aggregating operand, every part resolvable. If the\n"
    "        # call site could not be admitted => PRECOND-TOO-STRONG. Read back\n"
    "        # full ownership of the returned object's fields AND the identity of\n"
    "        # the value it supplies.\n"
    "        #\n"
    "        # The probe sits on the NO-FALLBACK path deliberately. That path runs\n"
    "        # at level 3 while the callee's with-fallback input demands level 2,\n"
    "        # so the self-call strictly DESCENDS and the recursion is well-founded\n"
    "        # (it also cannot recur again: the callee takes the return-c branch\n"
    "        # only when no fallback was requested, and here one is). On this input\n"
    "        # the Exsures condition is False, so the callee provably cannot\n"
    "        # reject and no handler is needed — the no-rejection domain is\n"
    "        # non-empty and contains the F2P cell.\n"
    "        plain = FallbackValue(True)\n"
    "        probe = resolve_aggregation(True, plain, False, False, None,\n"
    "                                    False, True, True, False, True)\n"
    "        Assert(Acc(probe.is_final_aggregation))\n"
    "        Assert(Acc(probe.supplies_fallback))\n"
    "        Assert(Acc(probe.wrapped))\n"
    "        Assert(Acc(probe.fallback))\n"
    "        Assert(probe.wrapped is not None)\n"
    "        Assert(probe.fallback is plain)\n"
)
_ADMISS_EXPR_PROBE = (
    "        # Admissibility self-call on the expression-valued-fallback cell (the\n"
    "        # P2P default=Avg('pages')/10.0): a fallback value that IS itself an\n"
    "        # expression and is NOT usable as written. Reads back all four facts\n"
    "        # of the resolution clause from the CALLER's side, which is only\n"
    "        # possible if that clause is satisfiable rather than contradictory.\n"
    "        # Same descending level as the other probe (3 -> 2).\n"
    "        written = FallbackValue(False)\n"
    "        yielded = FallbackValue(True)\n"
    "        probe = resolve_aggregation(True, written, True, True, yielded,\n"
    "                                    False, True, True, False, True)\n"
    "        Assert(Acc(probe.fallback))\n"
    "        Assert(probe.fallback is not written)\n"
    "        Assert(Acc(probe.fallback.usable))\n"
    "        Assert(Acc(probe.fallback.resolution_of))\n"
    "        Assert(probe.fallback.usable)\n"
    "        Assert(probe.fallback.resolution_of is written)\n"
    "        Assert(Acc(written.usable))\n"
    "        Assert(Acc(written.resolution_of))\n"
    "        Assert(not written.usable)\n"
    "        Assert(written.resolution_of is None)\n"
)
# Splice each probe into the GOLD body immediately BEFORE its `return c`, so the
# body is the gold decision verbatim plus the self-call and nothing else — the
# accept/reject verdict stays attributable to the added call alone.
_ADMISS_BODY = _swap(_GOLD_BODY, "        return c\n",
                     _ADMISS_PROBE + "        return c\n")
_ADMISS_EXPR_BODY = _swap(_GOLD_BODY, "        return c\n",
                          _ADMISS_EXPR_PROBE + "        return c\n")
for _c in SPEC_TESTS:
    if _c["id"] == "admiss-self-call":
        _c["module"] = _impl(_ADMISS_BODY)
        _c["rationale"] = (
            "the precondition must admit a normal F2P-shaped input: the final "
            "Sum-with-default after an annotate (requested_final=True, a fallback "
            "value that is not itself an expression and is usable as it stands, "
            "aggregating_operand=False, parts_resolve=True). The caller BUILDS "
            "that value, passes it, and reads back both the returned "
            "expression's fields and the identity of the value it supplies; if "
            "it could not => PRECOND-TOO-STRONG. It also shows the no-rejection "
            "domain is non-empty and contains the F2P cell."
        )
    if _c["id"] == "admiss-self-call-expression-fallback":
        _c["module"] = _impl(_ADMISS_EXPR_BODY)
        _c["rationale"] = (
            "the other side of the resolution branch must be admissible AND "
            "USABLE: an expression-valued fallback that is not usable as written "
            "(the P2P default=Avg('pages')/10.0 cell). The caller reads back all "
            "four facts of clause (P6) — the supplied value is a DISTINCT object, "
            "it is usable, it is the resolved form of the value that was passed, "
            "and that written value is unchanged. This is the non-vacuity control "
            "for (P6): the conjunction Acc(fallback.usable) and "
            "Acc(Result().fallback.usable) is satisfiable only because the two "
            "are different objects, so a caller consuming it proves the clause is "
            "a usable claim rather than a contradiction that would reject every "
            "rival for the wrong reason. If it could not verify => "
            "PRECOND-TOO-STRONG / SPEC-VACUOUS."
        )


# ---------------------------------------------------------------------------
# Axiom lane. There is NO @ContractOnly axiom and no consumed-axiom proof step in
# this bundle (meta.axioms == [], the axioms region is an empty singleton). The
# only callee-level obligation is the A-reference deep model of the resolution
# effect: (1) the unchanged super().resolve_expression stamps c.is_summary ==
# summarize (observed both bare and as the Coalesce's first source expression);
# (2) a `default` yields a DISTINCT Coalesce wrapper (model.py's supplies_fallback
# == True); (3) a fresh Coalesce defaults to is_summary == False (the unmarked
# state the added step repairs); (4) an expression-valued default resolves to a
# DISTINCT object that is compilable, while the written value is left exactly as
# it was (model.py's FallbackValue distinctness / usability / resolution_of). This
# is already host-validated by axiom_check.py / G-AX. We re-run that EXACT oracle
# IN-CONTAINER against the REAL Django classes: it imports django, builds real
# Sum/Avg/Min/Max/Count aggregates over a minimal model, and CALLS the real
# Aggregate.resolve_expression, reading the observed is_summary / isinstance /
# source-expression values (it does NOT regex source — pilot bug #4 avoided). The
# probe reads no container files (no utf-8 codec concern — pilot bug #5), and the
# runner mounts ONLY this probe script (axiom_check.py is embedded verbatim from
# the HOST at load time — pilot bug #6 avoided).
#
# apply_gold=False: the probe asserts ONLY unchanged-callee facts present in the
# BASE-COMMIT (pre-patch) image. It deliberately does NOT assert the returned
# wrapper's own is_summary — that propagation IS the added step and is absent
# pre-patch; asserting it would (correctly) FAIL on the base image. CONTAINMENT is
# vacuous: there is no @ContractOnly axiom domain, so no caller-reachable
# callee-input can fall outside one. The live obligation is A-reference soundness,
# which this probe checks against the real callee.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-resolution-effect",
        "axiom": "A-reference deep model of the resolution effect "
                 "(unchanged super().resolve_expression stamps c.is_summary == "
                 "summarize; default => distinct Coalesce wrapper; fresh Coalesce "
                 "defaults to is_summary == False; an expression-valued default "
                 "resolves to a DISTINCT compilable object and the written value is "
                 "left as it was)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness against the REAL Django callee in the "
                     "BASE-COMMIT image: the deep model of the resolution effect "
                     "(model.py's c = Expression(requested_final, False); a "
                     "DISTINCT wrapper on the fallback path with supplies_fallback "
                     "== True; the fresh wrapper's False default that the added step "
                     "repairs; and the FallbackValue facts — an expression-valued "
                     "default becomes a DISTINCT, compilable second source expression "
                     "while the written default object is unchanged) must equal what "
                     "the real Aggregate.resolve_expression produces over "
                     "Sum/Avg/Min/Max with a default and Count without, under both "
                     "summarize values. The probe CALLS the real callee (no source "
                     "scraping) and asserts ONLY unchanged-callee facts present "
                     "pre-patch (NOT the wrapper's own is_summary — that is the added "
                     "step). Any mismatch => the A-reference is unsound. No "
                     "@ContractOnly axiom exists, so containment is vacuous (no "
                     "axiom domain).",
    },
]
