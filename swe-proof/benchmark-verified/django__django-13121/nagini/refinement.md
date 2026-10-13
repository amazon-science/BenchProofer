# refinement.md — django__django-13121

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_arithmetic_path` and `operand_format_flag` impl regions) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** = proof uses the axiom; **A-reference**
= deep model validated == real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This bundle consumes **no `@ContractOnly` axioms**: both changed decisions are
modelled deeply over the finite integer abstraction of result-kind names and
dispatch targets. The corresponding real source is therefore an **A-reference**
(validated by G-AX), not a consumed axiom — there is no dead axiom.

## A. The dispatch site — `CombinedExpression.as_sql` (`expressions.py:443-459`)

Gold hunk (paraphrased): the duration guard `(lhs_output and ... == 'DurationField') or (rhs_output and ... == 'DurationField')` becomes `'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type`; the `output_field` objects become their `get_internal_type()` strings up-front; the temporal guard is rewritten over the type strings.

| # | model.py impl op (`select_arithmetic_path`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `lhs_kind, rhs_kind: int` | `lhs_type, rhs_type = self.lhs/self.rhs.output_field.get_internal_type()` (or `None` on `FieldError`) | R | result-kind name ↔ int code (mapping.md §2). `FieldError → None` ↔ `KIND_NONE`. The dispatch reads these only by `==`/`!=`/finite-set membership, preserved exactly by the int coding. |
| A2 | `native_duration: bool` | `connection.features.has_native_duration_field` | I | identical boolean. |
| A3 | `is_subtract: bool` | `self.connector == self.SUB` | R | the boolean value of the connector comparison; the model abstracts the connector to just "is it subtraction", which is the only property the two surviving guards read. |
| A4 | `if (not native_duration) and (lhs_kind == KIND_DURATION() or rhs_kind == KIND_DURATION()) and lhs_kind != rhs_kind: return PATH_DURATION()` | `if not has_native_duration_field and 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type: return DurationExpression(...).as_sql(...)` | R + I | `'DurationField' in {lhs_type, rhs_type}` ⇔ `lhs_kind == KIND_DURATION or rhs_kind == KIND_DURATION` (R); `lhs_type != rhs_type` ⇔ `lhs_kind != rhs_kind` (R); the conjunction and the chosen target `DurationExpression` ↔ `PATH_DURATION` are identical control flow (I). |
| A5 | `if is_subtract and is_temporal_kind(lhs_kind) and lhs_kind == rhs_kind: return PATH_TEMPORAL()` | `if self.connector == self.SUB and lhs_type in {'DateField','DateTimeField','TimeField'} and lhs_type == rhs_type: return TemporalSubtraction(...).as_sql(...)` | R + I | temporal-set membership ↔ `is_temporal_kind` (R); the guard + `TemporalSubtraction` ↔ `PATH_TEMPORAL` (I). Note `lhs_type in datetime_fields and lhs_type == rhs_type` already forces both non-None, matching the model. |
| A6 | `return PATH_PLAIN()` | fall-through to the plain `CombinedExpression` body (`compiler.compile` + `combine_expression`) | R | the plain rendering target ↔ `PATH_PLAIN`. The plain body itself is unchanged by the patch and produces the correctly-formatted SQL for the duration+duration case (mapping.md §3.1). |

The discriminating content of this hunk — duration+duration is now PLAIN, not
DURATION — lives in clause A4's added `lhs_kind != rhs_kind`. `model_prepatch.py`
drops it (pre-patch routed on *either* side being a duration) and **fails** the
postcondition `Implies(lhs == DURATION and rhs == DURATION, Result() != PATH_DURATION())`
— the spec sensing the change (G-DIFF, variant 1).

## B. The per-operand format site — `DurationExpression.compile` (`expressions.py:482-492`)

Gold hunk: the `if not isinstance(side, DurationValue):` exemption wrapping the
format decision is removed; the format wrapper now applies to any side whose
`output_field.get_internal_type() == 'DurationField'`, uniformly.

| # | model.py impl op (`operand_format_flag`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `operand_kind: int` | `side.output_field.get_internal_type()` (inside the `else` of the `FieldError` try) | R | result-kind name ↔ int code; `FieldError → None` ↔ `KIND_NONE` (which is `!= KIND_DURATION`, so no format — matching the `pass` branch). |
| B2 | param `is_literal: bool` | (post-patch: ABSENT — the `isinstance(side, DurationValue)` test is deleted) | R | the boolean the pre-patch branched on; post-patch the value of the decision is independent of it, which the spec pins by making `operand_format_flag`'s returned value a function of `operand_kind` ALONE. |
| B3 | `if operand_kind == KIND_DURATION(): return 1` else `return 0` | `if output.get_internal_type() == 'DurationField': return format_for_duration_arithmetic(sql), params` else fall through to plain `compiler.compile(side)` | R + I | `== 'DurationField'` ↔ `== KIND_DURATION` (R); "apply the format wrapper" ↔ return code `1`, "don't" ↔ `0` (I, an abstraction of the two return statements). |

The discriminating content — a *literal* duration operand is now formatted too —
lives in the absence of the `is_literal` exemption. `model_prepatch_2.py`
reinstates it (`if is_literal: return 0`) and **fails** the postcondition
`Result() == 1 if operand_kind == KIND_DURATION() else Result() == 0` on the
`(KIND_DURATION, is_literal=True)` input (G-DIFF, variant 2).

## C. The removed `date_interval_sql` overrides (no verifiable behaviour)

The gold patch also deletes the `date_interval_sql` method from
`BaseDatabaseOperations` and its MySQL/SQLite overrides, and the corresponding
`test_date_interval_sql` (a `NotImplementedError`-raising stub test). These are
**dead-code removals** consequential to deleting `DurationValue` (the only caller
of `date_interval_sql`). They carry no behaviour the F2P test observes and are
not modelled: removing an unreachable method changes no rendered SQL. They are
the necessary refactor that makes A/B sufficient (with `DurationValue` gone,
every operand is a plain `Value` and clause B is what decides its formatting).
Recorded here for completeness of the diff audit; tag: **I** (removal of dead
operations), no spec obligation.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I; the two genuinely-changed decisions
(`as_sql` dispatch, `compile` format) are modelled **deeply** over the finite
integer abstraction, not hidden behind a consumed axiom. There is no
`@ContractOnly` the proof consumes; the real source predicates are
**A-reference** decisions that G-AX validates the deep models against
(`axiom_check.py`, exhaustive + fuzz + end-to-end SQLite).

## E. verify(model) ⇒ resolved

`select_arithmetic_path` verifies only if it routes duration+duration to the
plain path (clause A4) and `operand_format_flag` verifies only if it formats
every duration operand including literals (clause B3). By R (kind-name ↔ int,
connector ↔ bool) the two verified decisions equal the gold patch's two
rewritten guards on every input; by G-AX the deep models equal the real
post-patch dispatch (A-reference) and the durations-only F2P scenario
round-trips on SQLite. Together with the dead-code removals of §C (no
behaviour), a model satisfying this spec refined by the map above is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
single trust point is refinement fidelity (this document, G-EQ) plus the
A-reference soundness check (G-AX); there is no axiom-soundness trust point
because no axiom is consumed.
