# mapping.md — django__django-15375

Binds every `model.py` symbol to its repository counterpart at
`base_commit = beb7ddbcee03270e833b2f74927ccfc8027aa693`, states the type
abstraction, and gives the provenance of the modelled behaviour (the
A-reference the deep model is validated against by axiom_check.py / G-AX).

Repo file under change: `django/db/models/aggregates.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_aggregation(requested_final, fallback, fallback_is_expression, resolution_yields_distinct, resolution_yield, aggregating_operand, operand_resolution_usable, condition_resolution_usable, vacuous_condition, parts_resolve)` | `Aggregate.resolve_expression(self, query, allow_joins, reuse, summarize, for_save)` — `django/db/models/aggregates.py:50-68` (whole body) | the modeled changed function (the aggregate resolver) |
| `Expression` / `self.is_final_aggregation` | a query `Expression`/`Func` object and its `is_summary` attribute (`BaseExpression.is_summary = False`, `django/db/models/expressions.py:155`) | the in-memory expression whose final-aggregation marking the change propagates |
| `Expression` / `self.supplies_fallback` | whether the returned object is the fallback `Coalesce` wrapper (yields the value when the aggregate matches nothing) vs the bare aggregate | pins the EXISTENCE of the fallback-supplying wrapper on the fallback path; `True` ⇔ a `Coalesce` is returned, `False` ⇔ the bare aggregate |
| `Expression` / `self.holds_own_fallback` | `expr.default is not None` — an `Aggregate` still carrying its own `default` that nothing supplies yet (`aggregates.py:63` reads it, `aggregates.py:67` clears it) | pins that the aggregation stops holding the value once the wrapper supplies it |
| `Expression` / `self.parts_usable` | every part the object is built from can be used as it stands: each of its source expressions, and (for an aggregation) a condition it still CARRIES — `filter is not None`, whether or not that condition restricts anything — has an `as_sql` (`BaseExpression.as_sql`, `expressions.py:191`; a raw `Q` has none). Concretely `conformance_check.py`'s `_parts_usable`: presence of the condition is what is read, NOT its truthiness, so an aggregation left carrying an empty (falsy) `Q` is `False` here | pins that the aggregation the wrapper exposes is the one resolution actually RESOLVED, not another object carrying the same marking |
| `Expression` / `self.fallback` | the SECOND source expression of the returned `Coalesce` — the value the wrapper actually supplies (`Coalesce(c, default, ...)`, `aggregates.py:68`; `Func._parse_expressions`, `expressions.py:184-189`) | pins WHICH value is supplied, by identity, not by a flag |
| `Expression` / `self.wrapped` | the FIRST source expression of the returned `Coalesce` — the resolved aggregation the wrapper supplies the value FOR (`aggregates.py:68`) | keeps the resolved aggregation observable through the wrapper, so its marking can be pinned too |
| `FallbackValue` | the `default` object as the fallback-supplying expression represents it: itself if it is an expression, else `F(default)` for a `str` and `Value(default)` otherwise (`Func._parse_expressions`, `expressions.py:186-188`) | the fallback value as a first-class object, so `Result().fallback is fallback` can be stated |
| `FallbackValue` / `self.usable` | `hasattr(x, 'as_sql')` — the value can stand as a fallback source as it is, without being resolved first (`BaseExpression.as_sql`, `expressions.py:191`; `F` has NO `as_sql`, `expressions.py:582-620`) | distinguishes a value that is compilable as it stands from a reference that must be resolved first |
| `FallbackValue` / `self.resolution_of` | the written value a supplied value is the resolution OF (`default = default.resolve_expression(query, allow_joins, reuse, summarize)`, `aggregates.py:65-66`) | pins the supplied value's PROVENANCE: it is the resolved form of the value that was asked for, not of anything else |
| `requested_final` | the `summarize` argument of `resolve_expression` (`aggregates.py:50`) | read-only flag: whether resolution is requested as a final/terminal aggregation |
| `fallback` (`None` or a `FallbackValue`) | `c.default` — `None` ⇔ no fallback requested (`(default := c.default) is None`, `aggregates.py:63`), else THE OBJECT that was written | the value itself, passed as an object |
| `fallback_is_expression` | `hasattr(default, 'resolve_expression')` (`aggregates.py:65`) | read-only flag: whether the value is put through resolution before it can be supplied |
| `resolution_yields_distinct` / `resolution_yield` | WHAT `default.resolve_expression(query, allow_joins, reuse, summarize)` RETURNED (`aggregates.py:66`) — a DIFFERENT callee, dispatched on the value's own class, so this resolution does not decide it: whether the returned object is a different one from the written value, and that object itself. Most classes build a new object (`c = self.copy()`, `expressions.py:246`); a value already in resolved form hands back the very object it was given (`return self` — `Ref`, `expressions.py:902-905`; `MultiColSource`, `fields/related_lookups.py:25-26`); an `OuterRef` over a nested `OuterRef` hands back its inner name, a bare `OuterRef` with NO `as_sql` (`expressions.py:645-648`) | read-only: the outcome of the delegated resolving step. All four combinations of (a distinct value came back, the value that came back is usable as it stands) are realizable through the public API |
| `aggregating_operand` | some source expression of the resolved aggregate has `expr.contains_aggregate` (`aggregates.py:57-59`) | read-only flag: the aggregation aggregates over another aggregation |
| `operand_resolution_usable` | WHAT PUTTING THE OPERAND THROUGH RESOLUTION CAME BACK WITH: whether the resolved form has an `as_sql`. `Func.resolve_expression` (`expressions.py:694-699`) delegates per operand to `arg.resolve_expression`, a DIFFERENT callee dispatched on the operand's own class, so this resolution does not decide it. Almost always usable (`F`/str → `Col`, `Value` → `Value`), but a step can succeed without raising and still come back with something that has NO `as_sql`: `OuterRef.resolve_expression` returns its inner name unchanged when that name is itself an `OuterRef` (`expressions.py:645-648`), leaving the aggregation carrying a bare `OuterRef` that cannot be compiled | read-only: the outcome of the delegated operand-resolution step, read for the same reason `resolution_yield` is on the fallback-value side. DISJOINT from `parts_resolve`, which tracks only whether a resolution RAISED: both values are realizable with `parts_resolve` true |
| `condition_resolution_usable` | WHAT PUTTING A CONDITION THAT RESTRICTS SOMETHING THROUGH RESOLUTION CAME BACK WITH: whether that resolved form has an `as_sql`. `aggregates.py:53` is `c.filter = c.filter and c.filter.resolve_expression(query, allow_joins, reuse, summarize)` — a call into a DIFFERENT callee dispatched on the WRITTEN condition's own class, so this resolution does not decide it, exactly as on the operand leg. Almost always usable (`Q` → `WhereNode`, `Exists` → `Exists`, `F` → `Col`, `Value` → `Value`), but a condition can be put through resolution without raising and still come back with something that has NO `as_sql`: `OuterRef.resolve_expression` returns its inner name unchanged when that name is itself an `OuterRef` (`expressions.py:645-648`), and `MultiColSource.resolve_expression` is `return self` (`fields/related_lookups.py:25-26`). `filter=` is not restricted to `Q` — `Aggregate.__init__` merely stores it (`aggregates.py:32`) and `:53` calls it — so this is ordinary usage, realizable as a nested `OuterRef` inside a doubly-nested `Subquery` | read-only: the outcome of the delegated CONDITION-resolution step, read for the same reason `operand_resolution_usable` and `resolution_yield` are. Immaterial where no such step runs (no condition, or `vacuous_condition`, which short-circuits `:53`'s `and`): nothing reads it there. DISJOINT from `parts_resolve`, which tracks only whether a resolution RAISED |
| `vacuous_condition` | the aggregation carries a restricting condition that was LEFT AS WRITTEN **and** whose written form has NO `as_sql`. "Left as written" is falsiness: a present `Q` with no children, which `Node.__bool__` makes FALSY (`django/utils/tree.py:60-62`), so the `and` at `aggregates.py:53` short-circuits and the condition is never replaced by a resolved one. The second half is required because falsiness does not imply uncompilability: a bare `WhereNode()` is equally childless and FALSY, so `:53` short-circuits on it too, but `WhereNode` DOES define `as_sql` (`django/db/models/sql/where.py:65`), so the aggregation it restricts IS usable as it stands and `_parts_usable` returns `True`. Measured on the gold-patched worktree: `Sum('num', filter=Q())` → `parts_usable False`; `Sum('num', filter=WhereNode())` → `parts_usable True`. Under a falsiness-only reading both abstract to the same input tuple while the real callee disagrees, i.e. the abstraction would not be a function; the conjunction restores it | read-only flag: an a-priori property of the WRITTEN condition (`filt is not None and not bool(filt) and not hasattr(filt, 'as_sql')`) |
| `parts_resolve` | every resolution the body performs SUCCEEDS: the operand (`aggregates.py:52`), the restricting condition (`:53`), an expression-valued value (`:66`), and — reached only when a value is supplied — the aggregate's own output type (`c._output_field_or_none`, `:68` → `expressions.py:272-282`, which RE-RAISES unless the field resolved to `None`). Error-type agnostic, because the observable is "the body reaches no expression": usually a `FieldError`, but the `:68` output-type read walks `Aggregate.get_source_fields` (`aggregates.py:38`), which asks each operand for `_output_field_or_none`, so an operand the delegated step handed back as a bare `OuterRef` makes it fail with `AttributeError` instead. Both are `parts_resolve` `False` | read-only flag: nothing the body must resolve fails |
| `ResolutionRefused` | an error escaping `resolve_expression` (`aggregates.py:62`, or propagated from `:52`/`:53`/`:66`/`:68`) — `django.core.exceptions.FieldError` on every leg except the `:68` output-type read, which can escape as `AttributeError` (see `parts_resolve` above) | no expression is produced for the aggregation at all |
| `c = Expression(requested_final, False)` | `c = super().resolve_expression(query, allow_joins, reuse, summarize)` (`aggregates.py:52`), which executes `c.is_summary = summarize` (`expressions.py:247`, and `:696` for `Func`) | the resolved aggregation |
| `c.parts_usable = (operand_resolution_usable and condition_resolution_usable and not vacuous_condition)` | the two resolutions `Aggregate.resolve_expression` performs ON the aggregation: the OPERANDS via `super().resolve_expression` (`aggregates.py:52` → `Func.resolve_expression`, `expressions.py:694-699`, which iterates `c.source_expressions` directly) and the CONDITION on the next line, `c.filter = c.filter and c.filter.resolve_expression(query, allow_joins, reuse, summarize)` (`aggregates.py:53`) | the resolved aggregation can be used as it stands. EACH of those can leave a part not usable as it stands, so ALL THREE outcomes are read rather than asserted: the operand resolution is delegated per operand to `arg.resolve_expression` and may come back with something that has no `as_sql` (`operand_resolution_usable`); the CONDITION resolution at `:53` is delegated on the condition's own class in exactly the same way and may likewise come back with something that has no `as_sql` (`condition_resolution_usable`); and a condition that restricts nothing is never resolved at all (`vacuous_condition`). The operand resolution ALONE also leaves a restricting condition a raw `Q` with no `as_sql`, which is why this is a separate observable from the marking |
| `supplied = resolution_yield` (with `resolution_yield.resolution_of = fallback` when a distinct value came back) / `supplied = fallback` otherwise | `default = default.resolve_expression(query, allow_joins, reuse, summarize)` (`aggregates.py:65-66`) — the rebound `default` is whatever that call returned, which is the written object itself for a value already in resolved form | putting a value that is itself an expression through resolution and supplying WHAT THAT YIELDED. The yield's usability is the delegated callee's outcome, not this one's |
| `wrapper = Expression(False, True)` then `wrapper.is_final_aggregation = c.is_final_aggregation` | `coalesce = Coalesce(c, default, output_field=c._output_field_or_none)` then `coalesce.is_summary = c.is_summary` (`aggregates.py:68-69` post-change) | the fallback wrapper and the propagating assignment (the change) |

The gold patch (the change, at `aggregates.py:68`) replaces
`return Coalesce(c, default, output_field=c._output_field_or_none)` with a
three-line form that names the wrapper, sets `coalesce.is_summary = c.is_summary`,
and returns it. Pre-patch, the `coalesce.is_summary = c.is_summary` line is
absent and the wrapper keeps the class default `is_summary = False`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a query `Expression`/`Func`/`Coalesce` object | `Expression` instance (minimal class, six observed fields) | the six fields below are exactly what the change and its surroundings read or write about the returned object |
| `is_summary` attribute (`bool`; class default `False`, `expressions.py:155`) | `is_final_aggregation` (`bool`) | `expr.is_summary` ↔ `expr.is_final_aggregation`; `True` ⇔ a final/terminal aggregation to be promoted to the outermost query scope |
| `isinstance(result, Coalesce)` — being the fallback wrapper vs the bare resolved aggregate | `supplies_fallback` (`bool`) | `True` ⇔ the returned object is the fallback-supplying wrapper; `False` ⇔ the bare aggregate |
| `getattr(result, 'default', None) is not None` — an `Aggregate` still carrying its own unwrapped `default` | `holds_own_fallback` (`bool`) | `True` ⇔ the expression still holds a fallback value that nothing supplies yet. `Coalesce` (a `Func`) has no `default` attribute at all, so a wrapper is always `False` |
| every source expression of the object, and a condition it still CARRIES (`filter is not None`, truthy or not), has an `as_sql` | `parts_usable` (`bool`) | `True` ⇔ the object can be used as it stands. For an aggregation this is what `aggregates.py:52` (operands) followed by `:53` (condition) establishes, and ANY OF THREE outcomes can leave a part not usable as it stands: the delegated operand step may come back with something that has no `as_sql` (`operand_resolution_usable`), the equally delegated CONDITION step at `:53` may come back with something that has no `as_sql` either (`condition_resolution_usable` — e.g. a nested `OuterRef`, `expressions.py:645-648`, or a `MultiColSource`), and a condition restricting nothing is never resolved at all (`vacuous_condition`). An aggregation obtained from the operand resolution ALONE carries resolved operands and a raw `Q` restricting condition, so it is `False` while still carrying `is_summary == summarize`. For the fallback wrapper the parts are the resolved aggregation — which always STANDS as a part, whatever the state of its own parts — and the value it supplies, so the wrapper's flag tracks the supplied value's |
| `result.get_source_expressions()[1]` — the value operand of the `Coalesce` | `fallback` (`Optional[FallbackValue]`) | `None` ⇔ no value is supplied (the bare-aggregate path); else the object the wrapper supplies |
| `result.get_source_expressions()[0]` — the aggregate operand of the `Coalesce` | `wrapped` (`Optional[Expression]`) | `None` ⇔ nothing is being wrapped; else the resolved aggregation the value is supplied for |
| the `default` object as `Coalesce` represents it: itself if an expression, `F(default)` for a `str`, `Value(default)` otherwise (`expressions.py:186-188`) | `FallbackValue` instance (minimal class, two observed fields) | object identity is the bijection: the model's `is` mirrors the repo's `is` (for an expression), and "carries that very object" (`Value.value is default`, `F.name is default`) for a plain value |
| `hasattr(x, 'as_sql')` | `usable` (`bool`) | `True` ⇔ the value can stand as a fallback source as it is. `BaseExpression`/`Func` have `as_sql` (`expressions.py:191`, `:701`); `F` does NOT (`expressions.py:582-620`) — it is a reference that `query.resolve_ref` must turn into a `Col` first (`expressions.py:595-597`) |
| the written value a supplied value came from | `resolution_of` (`Optional[FallbackValue]`) | `None` ⇔ the value is not the resolution of anything reachable here; else the value it is the resolved form OF. Concretely `supplied is not written` and `supplied` IS the object the delegated `written.resolve_expression(query, True, None, summarize)` handed back, read from that call rather than compared against a re-resolution: `__eq__`/`identity` are `Expression`'s (`expressions.py:392-422`) and the `Subquery` family extends `BaseExpression` instead, so for it equality against a re-resolution is object identity and would deny a provenance edge the real callee does establish |
| `summarize` argument (`bool`) | `requested_final` (`bool`) | identical boolean flag |
| `(default := c.default) is None` (the no-fallback early `return c`) | `fallback is None` → `return c` | `default is None` ⇔ `fallback is None`. NOT truthiness: `0`, `0.0`, `False`, `''` all take the fallback path |
| `expr.contains_aggregate` over the resolved source expressions (`aggregates.py:57-59`) | `aggregating_operand` (`bool`) | identical boolean fact about the operand |
| an error escaping the body (a `FieldError`, or the `AttributeError` the `:68` output-type read raises on an operand that has no `_output_field_or_none`) | `raise ResolutionRefused()` | rejection: no expression is produced. A user-defined exception is used because a builtin in an `Exsures` crashes the Nagini translator |
| `Coalesce(c, default, output_field=c._output_field_or_none)` construction | `Expression(False, True)` + `wrapper.wrapped = c` + `wrapper.fallback = supplied` | a fresh `Func` subclass instance inherits `BaseExpression.is_summary = False`, IS the fallback-supplying wrapper, and holds the two source expressions in that order. `output_field=` is not a field the model carries — but the resolution it PERFORMS is (see `parts_resolve`, next row) |
| `c._output_field_or_none` (`expressions.py:272-282`) evaluated at `aggregates.py:68` | folded into `parts_resolve` | it re-raises the `FieldError` from `output_field` (`:264-269`) unless `_output_field_resolved_to_none` was set, so an aggregate whose OWN output type cannot be determined resolves fine bare and is REJECTED once a value is supplied. This asymmetry is realizable (`Sum(F('num') + F('name'))`) and is generated by G-CONF |
| `c.default = None` reset (`aggregates.py:67`) | `c.holds_own_fallback = False` | the resolved aggregation stops holding the value once the wrapper supplies it |
| `c.filter` resolution (`aggregates.py:53`) | `c.parts_usable = True` (its SUCCESS) and `parts_resolve` (its FAILURE) | the condition's resolution has both a success effect — the aggregation becomes usable as it stands — and a failure mode, a `FieldError`, which is a rejection cause. Both are modelled, in the two places |
| the `FieldError` message text, `allow_joins`/`reuse`/`for_save` | omitted | not behaviour the change observes |

`super().resolve_expression(...)` (`Func.resolve_expression`,
`expressions.py:694-699`, over `BaseExpression.resolve_expression`,
`expressions.py:231-253`) is an UNCHANGED base method. The effects the model
depends on are `c = self.copy()` (`:246`) — so the aggregation as written is not
mutated — and `c.is_summary = summarize` (`:247`, `:696`). Both are reproduced
directly as `c = Expression(requested_final, False)` (refinement.md step A2) and
validated against the real callee by axiom_check.py (G-AX facts (1), (6)).

## 3. Provenance of the modelled effects (kind A-reference — checked by G-AX)

There is **no consumed `@ContractOnly` axiom** in this bundle (`model.py`'s
`axioms-start` region is empty). What follows are the unchanged-callee facts the
refinement reproduces concretely, each validated against the REAL Django code in
the BASE-COMMIT (pre-patch) image by `axiom_check.py`.

### 3.1 `is_summary` propagation ↔ real `Aggregate.resolve_expression`
**Callee context:** `Aggregate.resolve_expression`
(`django/db/models/aggregates.py:50-68`). From source:

- `c = super().resolve_expression(...)` → `Func.resolve_expression`
  (`expressions.py:694-699`) → `BaseExpression.resolve_expression`
  (`expressions.py:231-253`) executes `c.is_summary = summarize`
  (`expressions.py:247`, `:696`). So the resolved aggregate `c` carries
  `c.is_summary == summarize`.
- `is_summary` defaults to `False` at the class level
  (`BaseExpression.is_summary = False`, `expressions.py:155`); `Coalesce` is a
  `Func` and inherits that default, so a freshly constructed
  `Coalesce(c, default, ...)` has `is_summary == False` until assigned.
- The change assigns `coalesce.is_summary = c.is_summary`, so the returned
  wrapper carries `is_summary == summarize` — i.e. exactly when resolution was
  final.

**Why the marking matters (faithfulness, not consumed by the proof):** the
terminal-aggregation marking is read downstream when the query is split into an
inner subquery + an outer aggregate query (`django/db/models/sql/query.py:476`,
`get_aggregation`): expressions with `is_summary == True` are moved from the
inner subquery to the OUTER query. When an `annotate()` has already added an
annotation, the subquery path is taken (`query.py:404`), and a final aggregate
with a fallback — now a `Coalesce` — must have `is_summary == True` to be
promoted to the outer query. If it stays `False` it is stranded in the inner
subquery, the outer query selects nothing, and the backend emits the malformed
`SELECT FROM (subquery)` shown in the problem statement. The F2P test
`test_aggregation_default_after_annotation` exercises exactly this
`annotate(...).aggregate(..., default=...)` path.

### 3.2 WHICH value the wrapper supplies ↔ `Func._parse_expressions` / `aggregates.py:65-66`

- A value that is itself an expression is REPLACED by its resolution before
  wrapping: `default = default.resolve_expression(query, allow_joins, reuse,
  summarize)` (`aggregates.py:65-66`). The resolution is a distinct object (each
  `resolve_expression` starts from `c = self.copy()`, `expressions.py:246`; `F`
  resolves to a `Col` via `query.resolve_ref`, `expressions.py:595-597`), it is
  compilable as it stands (it has an `as_sql`), and the written object is left
  untouched. The model records this as a fresh `FallbackValue(True)` whose
  `resolution_of` is the written value.
- A value that is NOT an expression is passed to `Coalesce` as it is, and
  `Func._parse_expressions` (`expressions.py:184-189`) wraps it: a `str` becomes
  `F(str)` — a field REFERENCE with no `as_sql` — and any other plain value
  becomes `Value(v)`, which has one. Either way the wrapper carries THAT VERY
  OBJECT. **This is why no clause may assume a non-expression value is usable as
  it stands**: `default=''` is realizable and is represented as a field
  reference. An earlier draft of this spec required
  `Implies(fallback is not None and not fallback_is_expression, fallback.usable)`;
  the G-CONF differential produced `default=''` and refuted it, so the clause was
  removed rather than kept as a domain restriction (see refinement.md §B).

### 3.3 Soundness check (G-AX)
`axiom_check.py` configures Django with an in-memory sqlite database and a
minimal model (using the already-registered `contenttypes` app label — no
fabricated `INSTALLED_APPS` entry), then runs the REAL
`Aggregate.resolve_expression` under both `summarize` values. It asserts ONLY
**unchanged-callee facts present in the base-commit (pre-patch) image**:

1. the WRAPPED resolved aggregate (the first source expression of the `Coalesce`,
   and the bare aggregate on the no-fallback path) carries
   `is_summary == summarize` — set by the unchanged `super().resolve_expression`;
2. a `default` yields a DISTINCT `Coalesce` wrapper, not the bare aggregate — the
   unchanged fallback-wrapping structure (model.py's `supplies_fallback`);
3. negative control: a freshly constructed `Coalesce` defaults to
   `is_summary == False`;
4. an expression-valued `default` is supplied in RESOLVED form — a DISTINCT
   object, the very one the delegated `default.resolve_expression` handed back
   (read from that call, so a class carrying no structural equality is judged the
   same way as one that does), with an `as_sql`, and the written object left as
   usable as it arrived (§3.2);
5. a plain `default` is supplied as THAT VERY OBJECT (`Value.value is default` /
   `F.name is default`), and BOTH usability values are observed on that side of
   the flag — a written `str` becomes a field reference with no `as_sql` (§3.2);
6. the wrapped aggregation stops holding a fallback value of its own
   (`c.default = None`, `aggregates.py:67`) while the aggregation AS WRITTEN
   still holds it (`c = self.copy()`, `expressions.py:246`), and the returned
   wrapper holds none of its own;
7. EVERY part of the resolved aggregation is in resolved form — each of its
   source expressions AND the condition restricting it has an `as_sql` — both
   for the aggregation reachable through the `Coalesce` and for the bare one
   returned without a fallback. **Negative control for the same fact:** the
   operand resolution ALONE — `models.Func.resolve_expression(agg, query, True,
   None, summarize)`, which is exactly what `super().resolve_expression` runs at
   `aggregates.py:52` — resolves every operand, stamps the requested
   `is_summary`, and leaves the condition a raw `Q` with NO `as_sql`, because
   `Func.resolve_expression` iterates `c.source_expressions` directly
   (`expressions.py:694-699`) and the condition is resolved one line later
   (`aggregates.py:53`). So an aggregation that merely carries the right
   final-flag is NOT necessarily the aggregation resolution produced — which is
   what `model.py`'s `c.parts_usable = True` and the `Result().wrapped.
   parts_usable` clause record. (The check iterates the Func-level source list
   for the control, mirroring the repo's own `super(Aggregate, c).
   get_source_expressions()` at `aggregates.py:57`, because
   `Aggregate.get_source_expressions` APPENDS `self.filter`,
   `aggregates.py:40-44`.)

It deliberately does **NOT** assert the returned wrapper's own `is_summary` —
that propagation IS the change (`coalesce.is_summary = c.is_summary`), absent
before the patch; asserting it would make G-AX fail on the base image. A
configuration failure is a HARD ERROR (no silent swallow-and-pass), and the check
asserts `observations > 0`, so the gate cannot vacuously exit 0. It imports only
Django (the package the changed module lives in); nothing test-private. Exit 0
iff sound. (Confirmed on the BASE worktree: **42 observations**, all hold.)

The modelling is flag-independent: the `is_summary` propagation and the value
data-flow are the same on every backend; G-AX exercises the default `sqlite3`
backend the harness uses.

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: does the MODEL agree with the
REAL patched repo function?

**Shadow (provenance `direct`).** The `# impl-start` / `# impl-end` region of
`model.py`'s `resolve_aggregation`, copied VERBATIM with only the contract calls
removed — `Requires`/`Ensures` in the two constructors and the
`Assert(not wrapper.is_final_aggregation)` line. Control flow, variable names
(`c`, `supplied`, `resolved`, `wrapper`), the `if fallback_is_expression:` branch,
and the two-step `Expression(False, True)` → `wrapper.is_final_aggregation =
c.is_final_aggregation` sequence are preserved unchanged (verified line-for-line
against `model.py`). Collapsing those two steps into
`Expression(requested_final, True)` would be a paraphrase and would stop testing
that the real wrapper is born UNMARKED — the behaviour under specification. No
`@Pure` helpers and no `@ContractOnly` callees exist to bridge (§3), so no `PSeq`
shim is needed.

**Oracle: CALLED, not transliterated.** The real patched
`Aggregate.resolve_expression` (`django/db/models/aggregates.py:50`, §1). The
gate applies `patch.diff` to /testbed and sets `PYTHONPATH=/testbed`, so
`import django` resolves the patched module. Each probe builds a real
`Sum`/`Avg`/`Min`/`Max`/`StdDev`/`Variance`/`Count` over a real operand
(in-memory sqlite, `contenttypes` app label) and invokes
`agg.resolve_expression(query, True, None, summarize)`, then observes the
returned expression INCLUDING ITS SOURCE EXPRESSIONS. The patched tail is never
reimplemented — the check does not hardcode "a default yields a marked
Coalesce", nor which inputs raise: it asks the real object and compares. (The
velvet and lean siblings transliterate; on nagini the real function drives
cleanly in-container, so the stronger oracle is used.)

**Type bridge (§2, inverted).** Generation runs CONCRETE → ABSTRACT, and every
abstract input is computed from the WRITTEN construction alone — never from the
oracle's answer — so the bridge cannot echo the oracle:

| concrete realization | model input |
|---|---|
| the `summarize` argument | `requested_final` |
| `default is None` | `fallback is None` |
| the `default` OBJECT itself | `fallback` (a `FallbackValue` standing for it) |
| `hasattr(default, 'resolve_expression')` | `fallback_is_expression` |
| `hasattr(_as_coalesce_arg(default), 'as_sql')` — the written object as the fallback-supplying expression itself represents it (`expressions.py:184-189`) | `fallback.usable` |
| the operand contains an aggregate (a per-source a-priori fact of the space table) | `aggregating_operand` |
| `hasattr(written_operand.resolve_expression(...), 'as_sql')`, per source — the outcome of the per-operand callee `Func.resolve_expression` delegates to (`expressions.py:694-699`), read off the WRITTEN operand's own class: an `F` becomes a `Col`, while an `OuterRef` over a nested `OuterRef` hands back a bare `OuterRef` with no `as_sql` (`expressions.py:645-648`) | `operand_resolution_usable` |
| `hasattr(written_condition.resolve_expression(...), 'as_sql')` — the outcome of the DIFFERENT callee `aggregates.py:53` hands off to, obtained by calling it on the WRITTEN condition: a `Q` becomes a `WhereNode` and an `Exists` stays an `Exists`, while `MultiColSource.resolve_expression` is `return self` (`fields/related_lookups.py:25-26`), with no `as_sql`. Immaterial where no such step runs | `condition_resolution_usable` |
| `filt is not None and not bool(filt) and not hasattr(filt, 'as_sql')` — a present condition LEFT AS WRITTEN (childless, hence FALSY by `tree.py:60-62`, so `:53`'s `and` short-circuits and no resolving step runs) whose written form cannot be used as it stands. Both halves are load-bearing: a childless `WhereNode` is equally falsy and equally left as written but DOES define `as_sql` (`sql/where.py:65`), and the real callee keeps the aggregation's parts usable for it — under a falsiness-only reading the two would share one abstract input while the callee treats them differently. The realization space declares this column a priori and the harness recomputes it from the written object, so the two cannot drift | `vacuous_condition` |
| the operand names a real field ∧ the condition does ∧ an expression-valued default does ∧ (only when a default is supplied) the aggregate's own output type is determinable | `parts_resolve` |

| real returned expression | model output |
|---|---|
| `FieldError` raised | `ResolutionRefused` |
| `bool(result.is_summary)` | `is_final_aggregation` |
| `isinstance(result, Coalesce)` | `supplies_fallback` |
| `getattr(result, 'default', None) is not None` | `holds_own_fallback` |
| every source expression of the result — and its `filter`, when it has one — has an `as_sql` (`_parts_usable`) | `parts_usable` |
| source expression #0 | `wrapped` (and its five other fields likewise, `_parts_usable` included) |
| source expression #1 | `fallback` of the result |
| `s1 is default` (expression) / `s1.value is default` or `s1.name is default` (plain) | `Result().fallback is fallback` |
| `hasattr(s1, 'as_sql')` | `Result().fallback.usable` |
| `s1 is default.resolve_expression(...)` — the object that call returned, whichever it is | `Result().fallback is resolution_yield` |
| `s1 is not default` and `s1` IS what the delegated `default.resolve_expression(...)` handed back, recorded from that call | `Result().fallback.resolution_of is fallback` (claimed only on the arm where a DISTINCT value came back) |

The last three rows are the point of this gate for this cell. "The supplied
value is the RESOLVED one" is not a flag anyone reports — it is the identity of
the `Coalesce`'s second source expression, taken against the written object
itself (`is`) and against WHAT THE DELEGATED CALL HANDED BACK. That outcome is
RECORDED FROM THE CALL — the harness wraps `resolve_expression` on the written
value's own class for the duration of the real call and notes what it returned
for that object, returning it unchanged — and not reconstructed afterwards by
re-resolving and comparing. Equality is the obvious reading of it and it is the
wrong one: `__eq__` and `identity` are defined on `Expression`
(`expressions.py:392-422`), while `Subquery(BaseExpression, Combinable)`
(`expressions.py:1141`) and its `Exists` subclass inherit `object.__eq__`, so a
re-resolution of the very same written default never compares equal to the object
the real callee supplied — and the provenance edge would read as ABSENT on a
realization where the callee does establish it. Reading the call's outcome is one
test for every class in the hierarchy, and the realization space carries both
kinds (§G-CONF). A shadow that supplied the written value, or a value derived
from anything else, or one that is not compilable, disagrees on a real input.

**Third leg — the wrapper is born unmarked.** `wrapper = Expression(False, True)`
is untestable through the return value alone (the next line overwrites the
`False`). So on every fallback probe the check reconstructs a fresh wrapper from
the real returned `Coalesce`'s own sources
(`Coalesce(*result.get_source_expressions())`) and requires `is_summary is False`
— the model's `Expression(False, True)` and the stripped `Assert`. This is the
leg that makes a pre-patch oracle fail: without `coalesce.is_summary =
c.is_summary` the returned wrapper stays born-unmarked `False` while the shadow
reports `requested_final`.

**Fourth leg — the written value is left as it was.** After every probe with an
expression-valued default the check re-reads the WRITTEN object and requires it
is still exactly as compilable as it arrived — the concrete form of
`fallback.usable == Old(fallback.usable)`. An in-place resolution would be
invisible in the return value and is caught here.

**Inputs.** The MODEL's space is finite in its flags, so enumerating abstract
tuples would be weak; the enumeration is over the CONCRETE realization space —
aggregate kind × operand (plain field / composed / mixed-type / aggregate-
containing / nonexistent) × default kind (plain ints/floats/bools/strings,
expression-valued compilable and not, one over a nonexistent reference, and two
whose class implements no structural equality — the `Subquery` family) ×
filter (including one that does not resolve) × distinct × summarize —
exhaustively (**35376 cases**), then fuzzed over the same space with a pinned
seed to reach the budget (**100000**), for **135376 inputs total**. The end of the run
ASSERTS coverage of: both outcome classes; both final-flag values; both
`supplies_fallback` values; all FOUR realizable supplied-value shapes (none; the
written value, usable; the written value, NOT usable; the resolved form); both
`fallback_is_expression` values against both usability values; BOTH values of the
returned expression's `parts_usable` (a written `str` default is a field
reference with no `as_sql`, so the wrapper built over it is NOT usable as it
stands — the concrete witness that the flag is not a constant) and `{True}` for
the reachable aggregation's `parts_usable` on every fallback probe; three
rejection causes (a part that does not resolve, with and without an aggregating
operand; and the nested-aggregate rejection where every part does resolve); and
the ASYMMETRY that a mixed-type aggregate is PRODUCED bare and REJECTED once a
value is supplied; and that the two halves of `vacuous_condition` are realized
APART -- a condition LEFT AS WRITTEN that is nonetheless usable as it stands,
realized by a childless `WhereNode()` (falsy, so `aggregates.py:53`'s `and`
short-circuits and it is never resolved, yet it defines `as_sql`). That last one
is the near-miss control across the COMPILABILITY boundary: without it the space
would realize being left as written ONLY where that coincides with being
uncompilable, a falsiness-only reading of the input would be indistinguishable
from the faithful one over any number of inputs, and the gate could not catch a
regression to it. It ASSERTS as well that the PROVENANCE leg is realized on a
written default whose class implements no structural equality (`Subquery`,
`Exists`), and not only on the `Expression` subclasses that carry it: where it is
not, a recognizer that tests provenance by comparing against a re-resolution
agrees with one that reads the delegated call's own outcome on every input in the
space, and the difference between them — the difference between observing the
real callee and observing an accident of the class hierarchy — goes unmeasured.
So the script cannot pass vacuously.

**Pinned seed: `SEED = 15375`** (module constant), `N_FUZZ = 100_000`.
Exit 0 iff zero disagreements. Confirmed against the patched worktree:
135376 inputs, 0 disagreements. Negative control: run against the UNPATCHED base
commit the script exits 1 on the first `summarize=True` + `default=` probe (the
returned wrapper reports `is_summary == False` where the shadow reports `True`).
