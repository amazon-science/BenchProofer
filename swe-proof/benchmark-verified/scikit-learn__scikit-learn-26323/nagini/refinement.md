# refinement.md — scikit-learn__scikit-learn-26323

The operation-by-operation correspondence between `model.py`'s implementation
(the `set_output` impl region: the per-child configuration loop plus the
leftover-columns child write) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The configuration site — `ColumnTransformer.set_output` (`sklearn/compose/_column_transformer.py:275`)

Gold hunk (the behaviour-bearing addition):
```
  for trans in transformers:
      _safe_set_output(trans, transform=transform)

+ if self.remainder not in {"passthrough", "drop"}:
+     _safe_set_output(self.remainder, transform=transform)

  return self
```
(The other hunk is a single added blank line after `super().set_output(...)` —
cosmetic, no behaviour.)

| # | model.py impl op (`set_output`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `subs: List[Trans]` parameter | the children the generator yields: `trans for _, trans, _ in chain(self.transformers, getattr(self, "transformers_", []))` (filtered by the sentinel guard) | R | the materialized list of children ↔ the generator's yielded children (mapping.md §1, §2). |
| A2 | the `while i < len(subs)` loop with `if is_estimator(t): t.cfg = transform` | `for trans in transformers: _safe_set_output(trans, transform=transform)` | R + A-reference | the loop *structure* is the same fold over the children (R: list index ↔ generator iteration). The body `is_estimator(t) ⇒ t.cfg = transform` is the **deep model** of `_safe_set_output(trans, transform=transform)` (A-reference §3.1/§3.2 of mapping.md): configuring an estimator records the requested container; a sentinel is skipped. The real generator pre-filters sentinels; the model keeps them with `kind==0` and re-applies the guard — observationally identical (a sentinel is never configured either way). No consumed axiom. |
| A3 | `if is_estimator(remainder): remainder.cfg = transform` | `if self.remainder not in {"passthrough", "drop"}: _safe_set_output(self.remainder, transform=transform)` | R + A-reference | **the behaviour-bearing change.** `is_estimator(remainder)` (kind==1) ↔ `self.remainder not in {"passthrough", "drop"}` (A-reference §3.2). `remainder.cfg = transform` ↔ `_safe_set_output(self.remainder, transform=transform)` (A-reference §3.1). The deep model is the configuration write; G-AX validates both halves against the real callee + the real composite end-to-end. |
| A4 | (return `None`) | `return self` | I | the method returns the estimator for chaining; the model is a side-effecting procedure over the children. `self` identity is unchanged content (the F2P observes the children's configured containers, not the return identity). |

The discriminating content of the change — the leftover-columns estimator gets
configured — lives in step **A3**. `model_prepatch.py` drops the A3 write
(reproducing the bug: the loop configures only `subs`, never `remainder`) and
**fails** the postcondition `Implies(remainder.kind == 1, remainder.cfg ==
transform)`, which is exactly the spec sensing the change (G-DIFF). That clause
is what the downstream result-gathering relies on: an unconfigured
leftover-columns estimator returns a numpy array instead of the requested
DataFrame, so the composite's pandas-concat path is skipped — the F2P
`test_remainder_set_output` failure.

## B. No consumed axioms

The model consumes **no** `@ContractOnly` axiom (the `# axioms-start/end`
region is empty by design). The configuration propagation is modelled
**deeply**: a verified loop of field writes plus one extra write for the
leftover-columns child. The two unchanged repo callees the deep model abstracts
— the per-child configuration primitive `_safe_set_output` and the
estimator-vs-sentinel guard `trans not in {"passthrough","drop"}` — are
**A-references** (mapping.md §3), validated `deep model == real callee` by
axiom_check.py / G-AX, not consumed as axioms.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — also configuring the leftover-columns child when it is an estimator
— is modelled **deeply** (the A3 conditional write), not hidden behind an axiom
about the method under change. There is no consumed axiom anywhere.

## D. verify(model) ⇒ resolved

`set_output` verifies only if, after it returns, every estimator child AND the
leftover-columns child (when an estimator) carry the requested container code
(`cfg == transform`), while sentinels stay unconfigured (A2, A3, plus the
sentinel-unchanged postconditions). By R (children list ↔ generator,
`Trans.kind`/`Trans.cfg` ↔ estimator/`_sklearn_output_config`) the verified
procedure equals the gold `set_output` on the tested composite; by G-AX the
deep model `cfg = transform` equals the real `_safe_set_output` (A-reference)
and `is_estimator` equals the real sentinel guard (A-reference), confirmed
end-to-end on the issue's reproducer. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: callee-abstraction soundness (G-AX) and refinement
fidelity (this document, G-EQ).
