# refinement.md — django__django-15375

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_aggregation` impl region) and `patch.diff` (the gold patch) plus
its unchanged surroundings. Each step is tagged **R** (type refinement), **A**
(axiomatized callee — split into **A-consumed**, where the proof uses an axiom's
`Ensures`, and **A-reference**, where a deep model is validated == the real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. `Aggregate.resolve_expression` (`django/db/models/aggregates.py:50-68`)

Gold hunk (the change, at `aggregates.py:68`):
```
         c.default = None  # Reset the default argument before wrapping.
-        return Coalesce(c, default, output_field=c._output_field_or_none)
+        coalesce = Coalesce(c, default, output_field=c._output_field_or_none)
+        coalesce.is_summary = c.is_summary
+        return coalesce
```

The tail is reached only when a fallback `default` is supplied
(`(default := c.default) is None` is False, `aggregates.py:63`). Pre-patch, the
freshly constructed `Coalesce` wrapper inherits the class default
`is_summary == False` (`BaseExpression.is_summary = False`,
`expressions.py:155`), so a *final* aggregation (`summarize == True`) that has a
fallback is no longer marked final once wrapped. Downstream, the query splitter
(`sql/query.py:476`) only promotes `is_summary == True` expressions to the outer
aggregate query, so the unmarked `Coalesce` is stranded in the inner subquery,
the outer query selects nothing, and the backend emits the malformed
`SELECT FROM (subquery)` of the problem statement. The change copies the wrapped
aggregate's marking onto the wrapper.

The spec observes SIX fields of the returned expression —
`is_final_aggregation` (↔ `is_summary`), `supplies_fallback` (↔ being the
`Coalesce` wrapper), `holds_own_fallback` (↔ `expr.default is not None`),
`parts_usable` (↔ every source expression, and a condition the object still
CARRIES — `filter is not None`, truthy or not — has an `as_sql`), `fallback` (↔ the `Coalesce`'s SECOND source expression: the
value actually supplied) and `wrapped` (↔ its FIRST: the resolved aggregation) —
plus TWO fields of a fallback value: `usable` (↔ `hasattr(x, 'as_sql')`) and
`resolution_of` (↔ which written value it is the resolution OF). §B records what
each of the last four closes.

| # | model.py impl op (`resolve_aggregation`) | repo op (gold / surrounding unchanged code) | tag | justification |
|---|---|---|---|---|
| A1 | `Expression` with fields `is_final_aggregation`, `supplies_fallback`, `holds_own_fallback`, `parts_usable`, `fallback`, `wrapped`; `FallbackValue` with `usable`, `resolution_of` | the query `Expression`/`Func`/`Coalesce` objects, their `is_summary` / `default` attributes and their source expressions; the `default` object as `Coalesce` represents it | R | minimal classes carrying exactly the observed attributes (mapping.md §1, §2). The fallback value is a first-class OBJECT so that WHICH value is supplied can be stated by identity rather than by a flag. |
| A2 | `if not parts_resolve: raise ResolutionRefused()` | any error escaping the body: from the operand resolution (`aggregates.py:52`), the condition resolution (`:53`), an expression-valued default (`:66`), or `c._output_field_or_none` (`:68` → `expressions.py:272-282`, which re-raises unless the field resolved to `None`) | R | all four are "a part this resolution has to resolve cannot be resolved", folded into one input flag; reaching-no-expression ↔ `ResolutionRefused` (mapping.md §2). Error-type agnostic: a `FieldError` on every leg except the `:68` output-type read, which walks `Aggregate.get_source_fields` (`aggregates.py:38`) and so escapes as `AttributeError` when an operand — e.g. the bare `OuterRef` the delegated operand step hands back — has no `_output_field_or_none`. The fourth is reached ONLY when a value is supplied, which is why `parts_resolve`'s bridge conjoins the output-type term under `has_fallback` (G-CONF asserts the resulting asymmetry). |
| A3 | `c = Expression(requested_final, False)` | `c = super().resolve_expression(query, allow_joins, reuse, summarize)` (`aggregates.py:52`), which does `c = self.copy()` then `c.is_summary = summarize` (`expressions.py:246-247`, `:696`) | I (under R) | the unchanged base resolution's effects the change depends on are exactly those two: a DISTINCT resolved object, carrying `summarize`. Reproduced directly. The resolved aggregate is not itself a fallback-supplying `Coalesce`, so `supplies_fallback == False`. Validated by G-AX facts (1), (6). |
| A3b | `c.parts_usable = (operand_resolution_usable and condition_resolution_usable and not vacuous_condition)` | the resolution of the aggregation's PARTS: its operands, inside `super().resolve_expression` (`aggregates.py:52` → `Func.resolve_expression`, `expressions.py:694-699`, which walks `c.source_expressions` directly and delegates per operand to `arg.resolve_expression`), and its condition on the very next line — `c.filter = c.filter and c.filter.resolve_expression(query, allow_joins, reuse, summarize)` (`aggregates.py:53`) | I (under R) | the resolved aggregation can be USED as it stands. ANY of three outcomes can leave it not usable as it stands, so all three are read as inputs rather than asserted: the per-operand step is dispatched on the operand's own class and may come back with something that has no `as_sql` (`operand_resolution_usable` — `OuterRef.resolve_expression` hands back its inner name unchanged when that name is itself an `OuterRef`, `expressions.py:645-648`); the CONDITION step at `:53` is dispatched on the WRITTEN CONDITION's own class in exactly the same way, so it too may come back without an `as_sql` (`condition_resolution_usable` — the same nested-`OuterRef` behaviour, or `MultiColSource.resolve_expression`'s `return self`, `fields/related_lookups.py:25-26`), which is why the condition leg is a READ knob and not a function of falsiness alone; and a condition that restricts nothing is FALSY so `:53`'s `and` short-circuits and never resolves it, which leaves an unresolved part behind only when that WRITTEN condition has no `as_sql` (`vacuous_condition` is the conjunction of the two: left-as-written AND not compilable as written). Falsiness alone is not enough — a bare `WhereNode()` is childless and FALSY, so `:53` short-circuits on it as well, yet `WhereNode` defines `as_sql` (`django/db/models/sql/where.py:65`) and the aggregation stays usable as it stands (measured: `Sum('num', filter=Q())` → `parts_usable False`, `Sum('num', filter=WhereNode())` → `parts_usable True`). This is a separate observable from the marking because the two come apart in the real code: the operand resolution alone stamps `is_summary` and leaves a restricting condition a raw `Q` with no `as_sql`. Validated by G-AX fact (7) — including the negative control that `Func.resolve_expression` alone leaves the condition unresolved. §B5 records the rival this closes. |
| A4 | `c.holds_own_fallback = fallback is not None` | `c.default` is what `aggregates.py:63` reads: the resolved aggregation still carries the value at this point | R | modelled STATE, not a step of the work. A model that drops it claims the aggregation never holds a fallback of its own, which is false of the real callee (G-AX fact (6)), and can no longer describe leaving the value in place while wrapping — the state the `c.default = None` reset (A10) exists to prevent. |
| A5 | `if aggregating_operand and not requested_final: raise ResolutionRefused()` | `if not summarize: ... if expr.contains_aggregate: raise FieldError(...)` (`aggregates.py:54-62`) | R | identical guard; the message text is not observed (mapping.md §2). |
| A6 | `if fallback is None: return c` | `if (default := c.default) is None: return c` (`aggregates.py:63-64`) | R | `default is None` ⇔ `fallback is None`; identical early return of the resolved aggregation. NOT truthiness — `0`, `0.0`, `False`, `''` all continue (G-CONF generates all four). |
| A7 | `supplied = fallback`; `if fallback_is_expression: resolved = FallbackValue(True); resolved.resolution_of = fallback; supplied = resolved` | `if hasattr(default, 'resolve_expression'): default = default.resolve_expression(query, allow_joins, reuse, summarize)` (`aggregates.py:65-66`) | I (under R) | the local `default` is REBOUND to the resolution, and it is the rebound value that gets wrapped. The resolution is a distinct object (`c = self.copy()`, `expressions.py:246`; `F` becomes a `Col` via `query.resolve_ref`, `expressions.py:595-597`), it is compilable as it stands, and the written object is untouched — `FallbackValue(True)` with `resolution_of` set to the written value. When the value is NOT an expression, `supplied` stays the written object, which is what `Coalesce` then carries (`Func._parse_expressions`, `expressions.py:184-189`). G-AX facts (4), (5). |
| A8 | `wrapper = Expression(False, True)` | `coalesce = Coalesce(c, default, output_field=c._output_field_or_none)` (`aggregates.py:68`) | R | constructing the fallback wrapper — a DISTINCT expression that supplies the value. A fresh `Coalesce` (a `Func`) inherits `is_summary == False` (`expressions.py:155`). `output_field=` contributes no observed field, but the resolution it performs is folded into A2. |
| A8c | `wrapper.parts_usable = supplied.usable` | the wrapper's own parts are its two source expressions: `c` (resolved, hence usable — A3b) and the value being supplied, whose usability is `hasattr(_as_coalesce_arg(default), 'as_sql')` (`Func._parse_expressions`, `expressions.py:184-189`) | R | a `Func` is only as compilable as its sources: `Func.as_sql` compiles each one (`expressions.py:701-717`). So the wrapper is usable as it stands exactly when the value it supplies is. The equality is TWO-sided on purpose — over-claiming would let the unresolved-value rival of §B2 back in one level up, and under-claiming is refuted by the realizable `Sum('num', default=0)` (a `Value`, which HAS an `as_sql`). |
| A8b | `Assert(not wrapper.is_final_aggregation)` | (proof annotation, no repo counterpart — a runtime no-op) | R | pins the A8 modelled fact inside the proof: the freshly constructed wrapper is UNMARKED, exactly the G-AX negative control (3). A model variant whose wrapper is born already marked (`Expression(True, True)`) is unfaithful to the real callee and this assert makes it fail verification; it also kills the otherwise behaviourally-dead-store mutant `False -> True` on the construction line (G-MUT). It adds no postcondition strength: the frozen spec is byte-identical. |
| A9 | `wrapper.is_final_aggregation = c.is_final_aggregation` | `coalesce.is_summary = c.is_summary` | **I** (under R) | THE CHANGE. Identical concrete operation — copy the wrapped aggregation's `is_summary` onto the wrapper — with `is_summary` refined to `is_final_aggregation` (R). The single added behavioural statement of the gold patch. |
| A10 | `c.holds_own_fallback = False` | `c.default = None  # Reset the default argument before wrapping.` (`aggregates.py:67`) | I (under R) | the resolved aggregation stops holding a value of its own once the wrapper supplies it. G-AX fact (6). |
| A11 | `wrapper.wrapped = c` | `Coalesce(c, ...)` — `c` is source expression #0 of the wrapper (`aggregates.py:68`) | R | the resolved aggregation stays reachable through the wrapper, which is how its marking stays observable (mapping.md §2). |
| A12 | `wrapper.fallback = supplied` | `Coalesce(..., default, ...)` — the (possibly rebound) `default` is source expression #1 (`aggregates.py:68`) | R | the value the wrapper supplies IS the one arrived at in A7 — the written object, or its resolution. This is the identity the spec pins. |
| A13 | `return wrapper` | `return coalesce` | I (under R) | identical return of the now-marked fallback-supplying wrapper. |

**Statement order.** The repo performs A10 (`c.default = None`, `:67`) before A8
(constructing the wrapper, `:68`), while the model performs A8/A9 before A10. The
two orders are observationally identical: `c` and the wrapper are distinct
objects and nothing reads `c.default` in between. The G-CONF differential
observes the FINAL state of all five fields of the returned expression AND of the
aggregation reachable from it (so including `c`'s reset) on 105292 inputs with 0
disagreements, which is the measurement that this reordering is not a behaviour
change.

The discriminating content of the change lives in step **A9**.
`model_prepatch.py` drops A9 exactly as the pre-patch tail lacks the
`coalesce.is_summary = c.is_summary` line; with the byte-identical frozen spec it
**fails** verification on the postcondition
`Result().is_final_aggregation == requested_final` (`model_prepatch.py:204`),
which is precisely the spec sensing the change (G-DIFF).

## B. Where the spec senses the change (G-DIFF), and the three holes closed

`model_prepatch.py` is the pre-patch skeleton: it omits step **A9**. With the
byte-identical frozen spec it fails on
`Ensures(Result().is_final_aggregation == requested_final)`
(`model_prepatch.py:204` — `Assertion (Result().is_final_aggregation ==
requested_final) might not hold`). That is exactly what the F2P test observes:
`test_aggregation_default_after_annotation` (added by the test patch) runs
`Publisher.objects.annotate(double_num_awards=F('num_awards') * 2)
.aggregate(value=Sum('double_num_awards', default=0))` and asserts the result is
`40` rather than crashing with a malformed `SELECT FROM (subquery)`.

The postcondition is stated for BOTH `summarize` values and both fallback states
(it is `== requested_final` unconditionally), so a wrong impl cannot satisfy it
by hard-coding `True` only when convenient, nor by dropping the marking when no
fallback is present (the P2P `test_aggregation_default_*` cases without an
annotation, and `test_aggregation_default_not_in_aggregate`, still resolve a
non-final or final aggregate and must keep the correct marking).

### B1. `supplies_fallback` — the wrapper must exist
A spec pinning ONLY `is_final_aggregation == requested_final` is too weak: an
impl that returns the bare aggregation on the fallback path (`return c`, dropping
the `Coalesce`) verifies — `c.is_final_aggregation == requested_final` already —
yet does NOT resolve (the `test_aggregation_default_*` tests fail with
`None != <default>`). `Ensures(Result().supplies_fallback == (fallback is not
None))` pins the existence of the wrapper: `c` does not supply a fallback, so
`return c` FAILS verification (battery case `weak-return-bare-aggregate`).

### B2. `fallback` as a VALUE — the recorded refutation
The previous spec described the supplied value with a bare boolean
`fallback_resolved` — an attribute the IMPLEMENTATION writes about its own work.
Nothing tied it to the value actually supplied, so an impl could report
"resolved" while wrapping the value AS WRITTEN. That is the recorded G-EQ
refutation of this cell: a rival that keeps the flag but performs the wrapping
first verified against the old spec, and its repo counterpart fails P2P
`test_aggregation_default_passed_another_aggregate`
(`tests/aggregation/tests.py:1627`), which aggregates
`Sum('price', filter=Q(rating__lt=3.0), default=Avg('pages') / 10.0)` — an
expression-valued default that MUST be resolved before it can be wrapped, or the
`Coalesce` compiles an unresolved `CombinedExpression` over an unresolved `Avg`.

The repair removes the self-report entirely and replaces it with the VALUE, so
the claim is about data flow instead of narration:

* `Result().fallback is fallback` when the value needs no resolution (case (a));
* `Result().fallback is resolution_yield` when it is put through resolution
  (case (b)) — the value the delegated resolving step handed back, refined by
  (B6) below into the arm where that value is DISTINCT (`Result().fallback is
  not fallback` **and** `Result().fallback.resolution_of is fallback`) and the
  arm where the step handed back the very value it was given
  (`Result().fallback is fallback`).

Case (b)'s distinct arm also demands `Acc(Result().fallback.usable)` and
`Acc(Result().fallback.resolution_of)` on top of the `Acc(fallback.*)` the
precondition already holds. Two permissions to the same location are
unsatisfiable in Viper, so an impl that supplies the input object cannot prove
that arm at all — this is what makes "a DISTINCT object" enforceable rather
than merely stated on the arm where a distinct object is what came back. The rival above now fails with *There might be insufficient
permission to access Acc(Result().fallback.usable)* (battery cases
`weak-resolve-in-place`, `weak-unresolved-fallback-marker`,
`weak-self-resolution-cycle`, `weak-resolve-always`, `weak-echo-written-usability`,
`weak-drop-fallback-resolution`).

Non-vacuity of case (b) is proven, not assumed: battery case
`admiss-self-call-expression-fallback` calls the specified function from a caller
that reads back all four case-(b) facts and VERIFIES, so the conjunction is
satisfiable rather than a contradiction that would let anything through.

### B3. What the repair deliberately does NOT assume (the domain stays whole)
A first draft of the repair also required, as a PRECONDITION,
`Implies(fallback is not None and not fallback_is_expression, fallback.usable)`
— "a value that is not an expression can be used as it stands". The G-CONF
differential refuted it on a REALIZABLE input: `Sum('num', default='')`.
`Func._parse_expressions` (`expressions.py:184-189`) represents a written `str`
as `F(str)`, a field REFERENCE, and `F` has no `as_sql`
(`expressions.py:582-620`), so such a value is NOT usable as it stands and is
still passed straight through. Adding that precondition would have excluded a
real input — a partial-domain guard, i.e. a weaker spec wearing a stronger
signature. It was removed. What took its place is strictly stronger and makes no
assumption: case (a) now claims the FRAME,
`fallback.usable == Old(fallback.usable)` and
`fallback.resolution_of is Old(fallback.resolution_of)` (likewise in case (b) and
in the `Exsures`), so an impl may not repair the value in place to make its own
postcondition easier. G-AX fact (5) records both usability values on the
non-expression side, and G-CONF asserts coverage of all four realizable
supplied-value shapes.

### B5. `parts_usable` — the aggregation must be the one that was RESOLVED
The round-1 repair pinned WHICH VALUE the wrapper supplies. It left the OTHER
source expression under-described: `wrapped` was only "an `Expression` carrying
the requested final-flag, supplying no fallback, holding none of its own, with no
further wrapped aggregation". A freshly BUILT expression satisfies all of that.
The G-EQ audit found the corresponding freedom: three same-spec impls that
VERIFY, whose faithful refined patches do NOT resolve (measured `resolved=False,
attempts=3, flaky=False` each). All three substitute a second, bare
`super().resolve_expression(query, allow_joins, reuse, summarize)` for `c` when
building the `Coalesce`.

Why that breaks: `Func.resolve_expression` (`expressions.py:694-699`) iterates
`c.source_expressions` DIRECTLY, so it resolves the OPERANDS and never touches
`self.filter`. Resolving the condition is the next line of the function under
change — `c.filter = c.filter and c.filter.resolve_expression(query, allow_joins,
reuse, summarize)` (`aggregates.py:53`). A second bare base resolution therefore
yields an aggregation with the right `is_summary`, resolved operands, and a
condition that is still a raw `Q` with no `as_sql`. Every test that fails under
those patches carries a `filter=`: the P2P
`test_aggregation_default_passed_another_aggregate`
(`Sum('price', filter=Q(rating__lt=3.0), default=Avg('pages') / 10.0)`,
`tests/aggregation/tests.py:1627`) and the filtered datetime/time default cases.

The repair follows the same rule as B2 — make the unconstrained thing OBSERVABLE
rather than add a precondition. "Every part this expression is built from can be
used as it stands" becomes a sixth observable, `parts_usable` (↔ every source
expression, and a condition the object still CARRIES — `filter is not None`,
truthy or not — has an `as_sql`),
established by step A3b and claimed in three places:

* `Ensures(Implies(fallback is None, Result().parts_usable == (operand_resolution_usable and condition_resolution_usable and not vacuous_condition)))`
  — a returned bare aggregation is one resolution RESOLVED, and is claimed usable
  as it stands on exactly the inputs where the two delegated/short-circuiting
  steps above left it so;
* `Result().wrapped.parts_usable` — so is the aggregation the wrapper exposes;
* `Result().parts_usable == fallback.usable` (case (a)) and
  `Result().parts_usable` (case (b)) — the wrapper is usable exactly when the
  value it supplies is (A8c).

`Expression.__init__` establishes `not self.parts_usable`: merely BUILDING an
expression proves nothing about its parts, so whoever builds one is answerable
for them. That is what makes the substitution unprovable rather than merely
discouraged (battery cases `weak-fresh-inner-aggregation`,
`weak-fresh-inner-when-expression`, `weak-fresh-bare-return`,
`weak-never-resolve-parts`, `weak-overclaim-wrapper-parts`).

**Calibrated in both directions.** The clause forbids wrapping an aggregation
whose parts were never resolved — NOT wrapping a different aggregation. The
auditor's "generous" variant of the same rival re-resolves the condition after
the second base resolution and DOES resolve under the official harness (F2P 1/1,
P2P 95/95); its model analogue wraps a second aggregation with
`c2.parts_usable = True` and VERIFIES (battery case
`pos-control-second-full-resolution`). G-AX fact (7) supplies the other
direction: it asserts the real resolved aggregation's parts ARE usable, with the
operand-resolution-only negative control showing the two facts come apart in the
real code rather than being trivially co-extensive.

**Three parts, all read rather than asserted.** The clause says the aggregation is
usable as it stands exactly when the per-operand resolution came back with a form
that can be used as it stands, AND the condition resolution did too, AND no
condition that was left as written and cannot be used as it stands is still
carried. Claiming it UNCONDITIONALLY would
over-state what the function guarantees in three ways, on inputs that are ordinary
ORM usage and on which nothing raises.

* A condition restricting nothing is falsy, so `aggregates.py:53`'s `and`
  short-circuits and the condition survives exactly as written; it costs usability
  only when that written form has no `as_sql`, as a raw `Q` does. A `WhereNode()`
  is equally falsy but HAS `as_sql` (`django/db/models/sql/where.py:65`), so it
  survives without costing anything (`vacuous_condition` is the conjunction).
* The operand resolution is delegated per operand to `arg.resolve_expression`,
  which each operand class decides for itself: `OuterRef.resolve_expression` hands
  back its inner name unchanged when that name is itself an `OuterRef`
  (`expressions.py:645-648`), leaving the aggregation carrying a bare `OuterRef`
  with no `as_sql` (`operand_resolution_usable`).
* The CONDITION resolution is delegated in exactly the same way, and this is the
  leg it is easiest to get wrong: `aggregates.py:53` is `c.filter = c.filter and
  c.filter.resolve_expression(query, allow_joins, reuse, summarize)`, a call into a
  DIFFERENT callee dispatched on the WRITTEN CONDITION's own class. So the
  condition leg is NOT a function of falsiness alone — a condition can be truthy,
  be put through resolution, not raise, and still come back as something with no
  `as_sql`. `filter=` is not restricted to `Q`: `Aggregate.__init__` merely stores
  whatever it is given (`aggregates.py:32`) and `:53` calls it. Measured on the
  gold-patched worktree, `Sum('num', filter=OuterRef(OuterRef('num')))` resolves
  normally and leaves the aggregation carrying a bare `OuterRef`, so its parts are
  NOT usable as they stand while nothing rejected; `MultiColSource` as the
  condition does the same via `return self` (`fields/related_lookups.py:25-26`).
  Hence `condition_resolution_usable`. Where no such step runs at all — no
  condition, or one restricting nothing — there is no outcome of it to hold
  against the aggregation, so the flag is immaterial and no clause reads it there.

All three are read as inputs for the same reason `resolution_yield` is on the
fallback-value side (§B6) — a step this resolution hands off decides them — and
none weakens the discrimination the clause exists for: the rivals of the paragraph
above are all caught on operands AND conditions whose resolution DOES come back
usable and conditions that DO restrict something, which is what every
`filter=`-carrying P2P test in `tests/aggregation/tests.py` uses. The equality
stays TWO-SIDED on every leg, so an impl that claims usable parts where a
delegated step did not deliver them, and one that never resolves the parts at all,
both still fail.

### B6. What resolving the fallback value YIELDS is read, not asserted
The round-2 spec routed the supplied value on `fallback_is_expression` alone and
then asserted, of every input on that side, that a DISTINCT and USABLE value was
supplied. That is an over-claim: `default = default.resolve_expression(query,
allow_joins, reuse, summarize)` (`aggregates.py:66`) is a call into a DIFFERENT
callee, dispatched on the written value's own class, and this resolution neither
performs nor constrains it. Two of its outcomes break the old claim, and both are
reachable through the public API:

* **it can hand back the very object it was given.** `Ref.resolve_expression` is
  `return self` (`expressions.py:902-905`, "the sub-expression `source` has
  already been resolved") — a value already in resolved form is its own resolved
  form. `MultiColSource.resolve_expression` likewise
  (`fields/related_lookups.py:25-26`). Measured on the gold-patched worktree with
  `Sum('num', default=Ref('tot', Sum('books__pages')))`: the `Coalesce`'s second
  source IS the written object, so `Result().fallback is not fallback` and
  `Result().fallback.resolution_of is fallback` are both false of the real callee.
  `Pub.objects.annotate(tot=Sum('books__pages')).aggregate(v=Sum('num',
  default=Ref('tot', Sum('books__pages'))))` executes and returns a row.
* **the value it hands back need not be usable as it stands.**
  `OuterRef.resolve_expression` returns its inner name when that name is itself an
  `OuterRef` (`expressions.py:645-648`), yielding a bare `OuterRef` with no
  `as_sql`. So `Result().fallback.usable` and the unconditional
  `Result().parts_usable` are false of the real callee there.

The repair follows the same rule as B3 and B5 — make the thing this resolution
does not decide OBSERVABLE rather than assert it, and never restrict the domain.
Two inputs carry the delegated step's outcome: `resolution_yields_distinct`
(whether a different object came back) and `resolution_yield` (the object that
came back). Case (b) now pins the supplied value by IDENTITY to that yield —
`Result().fallback is resolution_yield` — and splits into (P6a), the arm where a
distinct value came back, which still demands the provenance edge and the fresh
permission that makes distinctness enforceable, and (P6b), the arm where the step
handed back what it was given, which supplies that value as it arrived. The
wrapper's own parts are usable exactly when the value it supplies is, on BOTH
arms, by the same two-sided rule case (a) already used.

**This gives up no discrimination.** (P6a) is what the three recorded G-EQ rivals
and `weak-drop-fallback-resolution` / `weak-resolve-in-place` /
`weak-unresolved-fallback-marker` / `weak-echo-written-usability` /
`weak-self-resolution-cycle` fail, and every one of them is exercised by an input
whose resolving step DOES yield a distinct value — including the P2P cell
`test_aggregation_default_passed_another_aggregate`
(`Sum('price', filter=Q(rating__lt=3.0), default=Avg('pages') / 10.0)`,
`tests/aggregation/tests.py:1627`), whose `CombinedExpression` resolves via
`c = self.copy()` (`expressions.py:513`). No test in `tests/aggregation/tests.py`
passes a `Ref` or a nested `OuterRef` as `default`, so the arm added here is
outside what the benchmark's tests observe while being inside what the callee
does. The differential now realizes all four (distinct, yield-usable)
combinations and asserts every one, so the enumeration cannot silently lose the
new arm.

### B4. Total, not partial
`Requires(MustTerminate(2 if fallback is not None else 3))` obliges resolution to
ANSWER on every admitted input — by producing an expression or by rejecting —
so the `Ensures`/`Exsures` are total-correctness claims. Nothing about the input
is restricted: every combination of the inputs is admitted (the single other
precondition is the `Acc` ownership of the passed value's two fields, which the
postcondition and the `Exsures` both hand back with the value unchanged), and the
`Exsures` specifies the rejecting inputs rather than excluding them. The level
rises to 3 on the no-fallback path purely so that a self-call from that path onto
a with-fallback input strictly descends, keeping such a recursion well-founded
(battery cases `admiss-self-call`, `admiss-self-call-expression-fallback`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference (via the G-AX validation of A3/A3b/A7/A8/A10's
modelled effects), or I. The operation that genuinely *changed* — copying the
final-aggregation marking onto the fallback wrapper — is an **I** step (the very
same `coalesce.is_summary = c.is_summary` assignment, only the attribute refined
to a field by R). There is no deep fold and **no consumed `@ContractOnly`
axiom**: the unchanged base resolution's relevant effects and the unchanged
value-resolution step are reproduced concretely (A3, A7) and validated against
the real callee by G-AX (**A-reference**, mapping.md §3), not consumed as axioms.
We never axiomatize the function under change.

## D. verify(model) ⇒ resolved

`resolve_aggregation` verifies only if:

* (A2, A5) it rejects on exactly the inputs where a part it must resolve does not
  resolve, or a non-final resolution of an aggregation over an aggregation is
  requested — the `Ensures(parts_resolve)` /
  `Ensures(requested_final or not aggregating_operand)` pair with the `Exsures`
  makes this an exact-if-and-only-if, so it can neither over-refuse nor
  under-refuse (battery cases `weak-over-refuse-final-nested`,
  `weak-return-instead-of-refuse`);
* (A8, A11, A12) on the fallback path it returns a DISTINCT expression that
  supplies a value, with the resolved aggregation reachable from it;
* (A9, A3) the returned expression's marking equals `requested_final`, and so
  does the reachable aggregation's, whether or not a fallback is present;
* (A7, A12) the value it supplies is the written one itself when nothing about it
  needs resolving, and otherwise a distinct, usable value that is the resolution
  OF the written one — with the written value left exactly as it was;
* (A3b, A8c, A11) the aggregation it exposes is one whose PARTS were resolved —
  every source expression and the condition restricting it usable as it stands —
  and the returned expression's own parts are usable exactly when the value it
  supplies is;
* (A4, A10) nothing returned still holds a fallback value of its own.

By R (the expression objects and `is_summary` ↔ `is_final_aggregation`; the
`Coalesce`'s two source expressions ↔ `wrapped` / `fallback`; `expr.default is
not None` ↔ `holds_own_fallback`; `hasattr(x, 'as_sql')` ↔ `usable`; `summarize`
↔ `requested_final`; `default is None` ⇔ `fallback is None`) and the **I** steps
A3/A7/A9/A10/A13, the verified body equals the gold body on the tested inputs. By
G-AX the real base resolution copies the aggregation and stamps `summarize` on it
(A3), the resolved aggregation's operands AND condition are both in resolved form
while the operand resolution alone leaves the condition a raw `Q` (A3b, fact (7)
and its negative control), an expression-valued value is supplied in distinct
resolved form while the written one is untouched (A7), a plain value is supplied
as that very object (A7), the real wrapper inherits `is_summary == False` until
assigned (A8), and the wrapped aggregation stops carrying its own value (A10) —
so the modelled effects equal the real callee (A-reference). By G-CONF the whole modelled body
agrees with the REAL patched `Aggregate.resolve_expression` on 105292 concrete
realizations with 0 disagreements. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (here the A-reference G-AX check of the modelled effects) and
refinement fidelity (this document, G-EQ).
