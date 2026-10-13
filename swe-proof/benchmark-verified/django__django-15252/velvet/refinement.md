# refinement.md — django__django-15252

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `recordStoreGate` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — none here), or
**I** (identical concrete op). The R/I legs are mechanically refuted by
**G-CONF** (`conformance_check.py`, §4.1); there are no A legs, so G-EQ has only
the narrative + the boolean-abstraction faithfulness to audit.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The schema gate — `MigrationExecutor.migrate()` (`executor.py:98-100`)

Gold hunk:
```
-        # migrations.
-        self.recorder.ensure_schema()
+        # migrations, but don't create it if there are no migrations to apply.
+        if plan == []:
+            if not self.recorder.has_table():
+                return self._create_project_state(with_applied_migrations=False)
+        else:
+            self.recorder.ensure_schema()
```

| # | Solution.lean impl op (`recordStoreGate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `hasWork : Bool` | the `plan == []` test on the `plan` argument | R | `plan == []` ↔ `hasWork = false` (mapping.md §2). The gate observes `plan` only through this emptiness test. |
| A2 | `storePresent : Bool` | `self.recorder.has_table()` | R | identity on `Bool` (mapping.md §2); `has_table()` is an unchanged callee, used only as a boolean input — not a consumed contract. |
| A3 | `if !hasWork then (if !storePresent then earlyExit := true) else ensured := true` | `if plan == []: if not self.recorder.has_table(): return _create_project_state(...) else: self.recorder.ensure_schema()` | I | identical control flow. Outer test `plan == []` ⇔ `!hasWork`; inner `not has_table()` ⇔ `!storePresent`; the `else` arm performing `ensure_schema()` ⇔ `ensured := true`; the inner-true arm `return …` (skipping the rest) ⇔ `earlyExit := true`. The nested `if`/`else` is the Velvet-faithful spelling of the patch's nested `if`/`else` (no `else if`, no early return inside a loop — §SPEC_GUIDE banned list respected). |
| A4 | `GateOutcome.ensured` returned | "did `ensure_schema()` run this step" | R | identity on `Bool` (mapping.md §2). The F2P test `test_migrate_test_setting_false_ensure_schema` asserts `mocked_ensure_schema.assert_not_called()` in the `plan==[]` ∧ `not has_table()` case — exactly `ensured = false` there. |
| A5 | `GateOutcome.earlyExit` returned | "did the step short-circuit before `check_replacements()`" | R | identity on `Bool` (mapping.md §2). The F2P test `test_migrate_skips_schema_creation` asserts `assertNumQueries(0)` for `migrate([], plan=[])` with `has_table` mocked `False` — the early `return` is what makes the step issue zero queries (no `ensure_schema`, no further work). |

Discriminating content of the change — `ensured` is `false` (no schema effect)
exactly when `!hasWork`, and the step short-circuits (`earlyExit`) exactly when
`!hasWork && !storePresent`. The pre-patch always performed the effect
(`ensured := true` unconditionally) and never short-circuited
(`earlyExit = false`); `Solution_prepatch.lean` reproduces that and **fails**
BOTH `ensures` clauses (`r.ensured = hasWork` and
`r.earlyExit = (!hasWork && !storePresent)`) — G-DIFF.

## B. No second site

The fix is a single hunk in one function. The hints discuss a broader
`MigrationRecorder` router redesign, but the **gold patch** (the shipped
correctness oracle, and what F2P pins) is solely this schema-gate change.
Modeling it faithfully means modeling exactly this gate — no extra method.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — the conditional
governing the `ensure_schema` side effect plus the early exit — is modeled
**deeply** as the nested-`if` control flow in the impl region (steps A3–A5), not
hidden behind any axiom. There are **no consumed axioms** and **no A-reference
deep models**: the unchanged callees (`has_table`, `ensure_schema`,
`_create_project_state`, `check_replacements`) contribute only boolean inputs
and tracked effect-observations, and the gate's correctness is independent of
what they each compute. Hence `axiom_check.py` is vacuous (G-AX has nothing to
execute) and the full mechanical weight on the cross-language refinement falls
on **G-CONF**, which is rich here (the impl region is all I/R, `conf_skip=false`).

## D. verify(Solution) ⇒ resolved

`recordStoreGate` verifies only if `ensured = hasWork` (the schema effect runs
iff there is work) and `earlyExit = (!hasWork && !storePresent)` (short-circuit
iff nothing to record and no store). By R (`plan == [] ↔ !hasWork`,
`has_table() ↔ storePresent`, and the two effect-observation identities) the
verified gate performs exactly the patched `migrate`'s preparation phase on the
modeled domain; by G-CONF the I/R transliteration of the branch agrees with the
real patched `migrate`'s observed `(ensured, earlyExit)` over ≥10⁵ fuzzed
boolean inputs. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (plan §1.1 trust point #1 is
empty for this bundle); the only residual trust is the boolean abstraction of
`plan`/`has_table`/effects in mapping.md §2, which G-CONF falsifies if wrong.
