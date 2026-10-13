# refinement.md — django__django-13121

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectRenderer` `do` block and its deep model `dispatchNode`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed** /
**A-reference** (axiomatized callee — none here), or **I** (identical concrete
op). The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE; confirmed applies clean
at base_commit and identical to `instance.json` `patch`).

## A. The renderer-selection site — `CombinedExpression.as_sql`

The single F2P-observable behaviour the fix changes is the interval-branch
condition of the renderer selection. Gold hunk (the leading guards of
`as_sql`, `django/db/models/expressions.py:443`):

```
-        if (not connection.features.has_native_duration_field and
-                ((lhs_output and lhs_output.get_internal_type() == 'DurationField') or
-                 (rhs_output and rhs_output.get_internal_type() == 'DurationField'))):
+        if (
+            not connection.features.has_native_duration_field and
+            'DurationField' in {lhs_type, rhs_type} and
+            lhs_type != rhs_type
+        ):
             return DurationExpression(...).as_sql(...)
-        if (lhs_output and rhs_output and self.connector == self.SUB and
-            lhs_output.get_internal_type() in {'DateField','DateTimeField','TimeField'} and
-                lhs_output.get_internal_type() == rhs_output.get_internal_type()):
+        datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
+        if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
             return TemporalSubtraction(...).as_sql(...)
```

| # | Solution.lean impl op (`selectRenderer`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `native : Bool`, `conn : Connector`, `lt rt : Option FieldTag` | `connection.features.has_native_duration_field`, `self.connector`, `lhs_type`/`rhs_type` (`get_internal_type()` or `None` on `FieldError`) | R | type bijection (mapping.md §2). G-CONF supplies all four directly. None is `mut` (directive 5): the selection reads them and leaves them unchanged. |
| A2 | interval branch `native = false ∧ isIntervalMix lt rt → durationNode` | `not has_native_duration_field and 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type → DurationExpression` | I | `isIntervalMix lt rt` ≡ `'DurationField' ∈ {lt,rt} ∧ lt ≠ rt`. The CHANGED condition: the new `lt ≠ rt` conjunct. Transliterated concretely; G-CONF refutes any mismatch. |
| A3 | temporal branch `conn = minus ∧ isTemporalTag lt ∧ lt = rt → temporalNode` | `connector == SUB and lhs_type in {Date,DateTime,Time} and lhs_type == rhs_type → TemporalSubtraction` | I | unchanged guard, re-expressed against `lhs_type` (the post-patch refactor reads `lhs_type` not `lhs_output`; observationally identical). G-CONF covers it. |
| A4 | fall-through `→ combined` | the generic combine path (`compiler.compile` + `combine_expression`) | I | the default renderer; observable as `NodeKind.combined`. |
| A5 | output `out : NodeKind` | which renderer's `as_sql` produces the SQL | R | class ↔ constructor bijection (mapping.md §2). |

The discriminating content of the change — two interval-typed operands
(`lt = rt = durationTag`) must NOT take the interval branch — lives in the
`lt ≠ rt` conjunct of `isIntervalMix`. Pre-patch the interval branch fired on
`lt = durationTag ∨ rt = durationTag` with no inequality requirement, so
`F('estimated_time') + delta` (both `durationTag`, `native=False`) was routed to
the broken interval renderer (`date_interval_sql` → bare microseconds →
`decimal.ConversionSyntax`). `Solution_prepatch.lean` reproduces that buggy guard
and **fails** `out = dispatchNode …` exactly on the both-`durationTag` clause
(G-DIFF goal: `¬isIntervalMix (some durationTag) (some durationTag)`).

## B. Supporting refactors (R-refinements of the same selection — audit only)

The gold patch touches four files, but every hunk other than §A is a mechanical
refactor that preserves the dispatch decision modeled in §A (mapping.md §1.1):

| construct | patch.diff op | tag | justification |
|---|---|---|---|
| operand carries `durationTag` | `_combine` wraps a `timedelta` literal as `Value(other, output_field=DurationField())` instead of `DurationValue` | R | only determines that the literal's resolved tag is `durationTag` — an input to `selectRenderer`, captured by `lt`/`rt`. |
| (no node) | `DurationExpression.compile` drops the `isinstance(side, DurationValue)` short-circuit; `DurationValue` deleted; `date_interval_sql` / `duration_microseconds` removed | I (dead-code removal) | the broken interval renderer the buggy dispatch reached. Once two-duration sums route through the generic combine (§A), this path is unreachable for the F2P case; removing it is behaviour-preserving for the tested inputs. |

No separate failing prepatch for site B: these refactors are byte-identical-spec
neutral (a prepatch must keep the frozen spec; G-DIFF). The one independently
observable fixed behaviour — the interval-branch condition — is exercised by the
§A prepatch.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
renderer-selection condition — is modeled **deeply** (the spelled-out
`dispatchNode` / `isIntervalMix`, steps A2–A4, all I), not hidden behind an
axiom about the function under change. There is **no consumed axiom and no
A-reference**: the operand type tags are abstracted R-inputs (mapping.md §2),
and the downstream renderers are an unchanged shared continuation, not assumed.

## D. verify(Solution) ⇒ resolved

`selectRenderer` verifies only if its selected renderer equals `dispatchNode`
exactly — in particular two equal interval tags fall through to the generic
renderer (A2) and a difference of two equal point-in-time types selects the
temporal renderer (A3). By R (the type bijection of mapping.md §2) the verified
selection equals the patched `CombinedExpression.as_sql` dispatch on every
operand-tag/connector/native configuration; by G-CONF the R/I transliteration of
`dispatchNode` agrees with `patch.diff`'s behaviour on 144 boundary + 100 000
fuzzed configs. The supporting refactors (B) are behaviour-preserving for the
F2P inputs. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The sole trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point (no axioms).
