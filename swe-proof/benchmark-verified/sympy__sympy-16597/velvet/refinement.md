# refinement.md — sympy__sympy-16597

Operation-by-operation correspondence between `Solution.lean`'s model (the deep
theory `consistentTheory` and the two deducers `deduceEven` / `deduceInfinite`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-reference** (a deep model validated == the real callee by
conformance_check.py / G-CONF), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, deduces the same fact tables the gold patch deduces on the tested
seeds, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There is **no opaque consumed callee**: the changed behaviour — the
set-containment rule theory — is modelled DEEPLY (`consistentTheory`), so the
real rule engine is an **A-reference** (validated by G-CONF), not an oracle.

## A. The rule theory — `_assume_rules` (`sympy/core/assumptions.py:163-201`)

Gold behavioural delta (a boundedness conjunct added to four membership
consequents):

```
- rational       ->  real
+ rational       ->  real & finite
- algebraic      ->  complex
+ algebraic      ->  complex & finite
- transcendental ==  complex & !algebraic
+ transcendental ==  complex & !algebraic & finite
- irrational     ==  real & !rational
+ irrational     ==  real & !rational & finite
```

(the `ask_generated.py` hunk is the mechanically-recompiled CNF/dict mirror of
the same rules; `make_known_facts` regenerates it — it carries no independent
behaviour.)

| # | Solution.lean op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `KB` record of `Option Bool` fields, one per fact | the `StdFactKB`/`FactKB` dict of `is_<fact>` → True/False/None for a quantity | R | a fact value `some true`/`some false`/`none` ↔ `True`/`False`/`None`; one field ↔ one dict entry (mapping.md §2). |
| A2 | `consistentTheory k` — the conjunction of the containment implications including the new `rational/algebraic/irrational/transcendental → finite` edges and their contrapositives, plus the pre-existing engine edges (`integer → rational`, `real → complex`, the `¬odd` direction of `even ≡ integer ∧ ¬odd`, the reverse exclusion `integer → ¬noninteger`, …) | the post-edit `_assume_rules` rule set compiled by `FactRules`, whose closure `deduce_all_facts` enforces exactly these implications on every fact table | A-reference | the changed rule string is modelled **deeply** as the closure predicate; no opaque callee. The contrapositives (`¬finite → ¬rational…`, `¬rational → ¬integer`, `¬integer → ¬even/¬odd/¬prime/¬composite`) are exactly what `deduce_alpha_implications` adds (`facts.py:116`). The pre-existing edges over-cover the caller-reachable facts. G-CONF validates every clause of `consistentTheory` holds in the real engine across the singletons + all satisfiable single/pair seeds. |
| A3 | `deduceEven` (`evenTable`): seeds `even=true` and returns the closure assigning `integer/rational/real/algebraic/finite/complex = true`, `odd/noninteger = false`, with `consistentTheory evenTable` proved | the engine's forward-chaining closure of the seed `even=True` under the edited rules, deducing `is_finite=True`, `is_odd=False`, `is_noninteger=False` | R + A-reference | each fired implication edge ↔ one field value (mapping.md §2). The discriminating edge `rational → finite` is **new**; the table sets `finite = some true` because rational forces it. `odd=false` / `noninteger=false` are the pre-existing `even ≡ integer ∧ ¬odd` and `integer → ¬noninteger` deductions. The closure result is what both compute. |
| A4 | `deduceInfinite` (`infiniteTable`): seeds `infinite=true, real=true` and returns the closure assigning `complex=true`, `finite=false`, and (via the contrapositives) `rational/integer/even/odd/algebraic/transcendental/irrational/composite=false`, `noninteger=true`, with `consistentTheory infiniteTable` proved | the engine's closure of an unbounded-real seed under the edited rules, deducing `is_complex=True`, the set memberships False, `is_noninteger=True` | R + A-reference | the new edges make `¬finite` (from `infinite`) propagate to `¬rational` etc. (contrapositives of A2), then `¬rational → ¬integer → ¬{even,odd,prime,composite}`. `complex=true` is the pre-existing `real → complex` deduction. The closure result is identical. |

## B. The discriminating clause and the prepatches

The behavioural change is **two** independently-observable deductions, so there
are two prepatch variants, each reverting one deducer's impl region to the
pre-patch propagation (the old rule set has no `* → finite` edges):

- `Solution_prepatch.lean` reverts `deduceEven`: it stops at the pre-patch
  `rational → {real, algebraic}` and leaves `finite = none`. It **fails**:
  `consistentTheory` now requires `rational=true → finite=true`, and the
  witnessed postcondition `out.finite = some true` is unmet (the prover is left
  the unprovable goal `none = some true`). (G-DIFF, behaviour 1.)
- `Solution_prepatch_2.lean` reverts `deduceInfinite`: `infinite → ¬finite`
  fires (`finite = some false`) but `¬finite` propagates to nothing under the
  old rules, so `rational/integer/even/…` stay `none`. It **fails**:
  `consistentTheory` now requires `finite=false → rational=false` (and the
  cascade), and the witnessed postconditions `out.rational = some false`,
  `out.integer = some false`, … are unmet (again `none = some true/false`).
  (G-DIFF, behaviour 2.)

Both fail on the closure postcondition `consistentTheory out`, the **tightest**
witness: it senses the missing rule edges at the level of the whole theory,
subsuming the individual fact assertions. The shared spec (`KB`,
`consistentTheory`, the deducers' pre/post regions) is byte-identical across all
three files (verified by `same_spec`); only the two impl regions differ, one per
prepatch.

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R or A-reference. The one operation that genuinely *changed* —
the rule theory (the `* → finite` containments) — is modelled **deeply** as
`consistentTheory` and the deducers' closed tables, not hidden behind an oracle
about the engine. The real engine (`FactKB.deduce_all_facts` over the edited
`_assume_rules`) appears only as the **A-reference** G-CONF validates the deep
model against. There is no opaque consumed callee.

## D. verify(model) ⇒ resolved

`deduceEven` / `deduceInfinite` verify only if their returned tables are closed
under `consistentTheory` (A2) — which forces `finite=true` for the even seed and
the full False-cascade + `noninteger=true` for the unbounded-real seed, i.e.
exactly the F2P-observed deductions. By R (trit ↔ `Option Bool`, dict ↔ record,
`deduce_all_facts` closure ↔ the returned closed table) the verified deducers
compute the same fact tables the real engine computes under the edited
`_assume_rules`. By G-CONF the deep theory `consistentTheory` holds in the real
post-patch engine (and fails pre-patch), so the model's theory IS the gold rule
set's closure on the tested seeds. The gold patch (which edits exactly those
rules) resolves (G-RESOLVE). The trust points are A-reference soundness (G-CONF)
and refinement fidelity (this document, G-EQ).
