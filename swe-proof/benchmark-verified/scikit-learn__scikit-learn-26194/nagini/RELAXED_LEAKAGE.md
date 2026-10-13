# RELAXED-LEAKAGE ACCEPTANCE: scikit-learn__scikit-learn-26194

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14).** This instance is a `problem_statement <-> gold` MISMATCH: the
public issue proposes one fix direction (clip the thresholds so none exceed 1),
while the gold patch + the committed F2P test require the OPPOSITE concrete
discriminator — the leading anchoring threshold is the POSITIVE-INFINITY
sentinel `np.inf`. The discriminating vocabulary of the gold fix (`np.inf` /
`np.isinf` / "infinite leading threshold") appears ONLY in the gold patch and
the hidden `test_patch`, never in the solver-visible `problem_statement` (and
not in `hints_text` either). Any FAITHFUL spec must pin the infinite leading
element (else the prepatch would not fail — G-DIFF, and a "clip to <= 1" impl
would wrongly verify), but no spec derivable from the `problem_statement` alone
can name `np.inf`, because the public issue is about *clipping down to 1* and
never about an infinite sentinel. Faithful + non-leaking is therefore provably
impossible here.

Per the project's relaxed-leakage policy (see `RELAXED_LEAKAGE.md`), such
PS<->gold-mismatch instances are KEPT in the verified set with the gold-derived
discriminator allowed in the spec view, rather than excluded. The
"verify => correct" guarantee is UNAFFECTED (the core is sound and the gold
resolves); only the no-leakage property is relaxed for this documented instance.
The adversarial mismatch analysis is retained below as the rationale.

---

## Why this is not a de-narration fix (the leak is the behavior, not narration)

The soundness axes are clean and were re-verified here (see "Re-verify snapshot"
below) — the bundle is *sound and tight*. The mechanical G-LEAK screen also
passes (no diff line, no patched path `sklearn/metrics/_ranking.py`, no patched
symbol `roc_curve`/`np.r_`, no `+1` rule, no bug->fix narration; the spec view
describes the abstract behavior "anchor the ROC curve at the origin with a
positive-infinity leading threshold"). The relaxation is needed because the
**semantic** discriminator the spec must pin to be faithful — that the leading
threshold is `+inf` — is itself absent from the public issue and present only in
the gold/`test_patch`.

### The gold took the OPPOSITE direction from the public issue's proposal

Gold patch (`sklearn/metrics/_ranking.py`, the threshold-anchoring site):

```python
-    thresholds = np.r_[thresholds[0] + 1, thresholds]
+    # get dtype of `y_score` even if it is an array-like
+    thresholds = np.r_[np.inf, thresholds]
```

The discriminator is **the leading anchoring threshold is the positive-infinity
sentinel `np.inf`** (was the finite `max(y_score) + 1`). The committed F2P test
`test_roc_curve_with_probablity_estimates` asserts exactly `np.isinf(thresholds[0])`,
and `test_roc_curve_drop_intermediate` expects `[np.inf, ...]` at index 0.

### That discriminator is absent from (in fact contradicted by) the public PS

Token check (case-insensitive over the solver-visible `problem_statement`):

- `inf` -> ABSENT, `isinf` -> ABSENT, `np.inf` -> ABSENT.
- `clip` -> PRESENT, `above 1` -> PRESENT, `+ 1` -> PRESENT.

The `problem_statement` frames the defect as "`roc_curve` returns a threshold
greater than 1 for probability estimates" and proposes a fix in the OPPOSITE
direction:

> "A potential workaround would be to check `thresholds.max() <= 1` in which
> case we should clip `thresholds` to not be above 1."

So the public issue's own proposed remedy (clip down so the max threshold is
<= 1) is *incompatible* with the gold (which makes the leading threshold `+inf`,
i.e. arbitrarily large). The PS even ships a candidate non-regression test that
asserts `np.logical_or(thresholds <= 1, thresholds >= 0).all()` — a vacuous
predicate (every real satisfies `r >= 0 or r <= 1`) that does NOT mention
infinity. The actual committed test was changed to the infinite-leading-element
assertion. A `problem_statement`-only solver would reach for clipping/`min`,
never for prepending `np.inf`.

- `hints_text` check: `inf` / `isinf` / `np.inf` all ABSENT there too — so the
  discriminator lives ONLY in the gold patch and the hidden `test_patch`.

### Any faithful spec must pin the leaked discriminator

To satisfy G-DIFF / G-EQ / faithfulness, `model.py` must pin the gold's actual
behavior: the leading anchoring threshold satisfies `is_pos_inf(Result()[0])`
(the model of `np.isinf(thresholds[0])`), with the remaining elements the
unchanged input thresholds in order. That infinite-leading-element behavior IS
the gold's tested discriminator (F2P `test_roc_curve_with_probablity_estimates[42]`
asserts `np.isinf(thresholds[0])`; F2P `test_roc_curve_drop_intermediate`
expects `np.inf` at index 0). There is no PS-derivable (clip-to-<=1)
reformulation that still models the gold fix, because the gold fix swaps the
finite sentinel for an INFINITE one — the opposite of clipping down. The
prepatch (which uses the finite `thresholds[0] + 1`) FAILS exactly this clause
(`model_prepatch.py:72`, `is_pos_inf(Result()[0])` might not hold) — proving the
discriminator is load-bearing and unavoidable.

## Re-verify snapshot (soundness intact — this is a relaxation, not a defect-in-spec)

- G-VERIFY: PASS — `model.py` verifies with `--float-encoding=real`, 29.87s
  (< 300s).
- G-DIFF: PASS — `model_prepatch.py` FAILS at `model_prepatch.py:72:13`
  (`Postcondition of anchor_thresholds might not hold. Assertion
  is_pos_inf(Result()[0]) might not hold`), the named counterexample (prepatch
  uses the finite `thresholds[0] + 1.0`, which is not the infinite sentinel).
- same_spec: TRUE — spec regions (axioms/pure/pre/post/invariants) AND the module
  docstring are byte-identical between `model.py` and `model_prepatch.py`; only
  the `impl` region differs (`lead = pos_inf()` vs `lead = thresholds[0] + 1.0`).
- Static gates (G-INTEGRITY / G-HYGIENE / G-LEAK-mechanical): pass.
- G-AX: SOUND — two A-consumed axioms (`pos_inf` <-> `np.inf`, `is_pos_inf` <->
  `np.isinf`). `axiom_check.py` validates the axiom callees UNCONDITIONALLY
  (patch-state-independent: `np.isinf(np.inf)` True, `np.inf > 0`, finite reals
  and `finite + 1.0` not infinite) and runs RC=0 in the default pre-patch eval
  container; the real-`roc_curve` end-to-end faithfulness leg is gated on gold
  being applied and passes RC=0 there (9 boundary + F2P seed-42 fixture + 5000
  fuzz inputs).
- G-RESOLVE: `patch.diff` == gold verbatim (1850 B), applies at `base_commit`;
  resolves F2P `test_roc_curve_drop_intermediate` + `test_roc_curve_with_probablity_estimates[42]`
  + P2P. Docker oracle by orchestrator.

The mechanical G-LEAK screen passes (no diff lines/paths/narration), but it is
lexical and blind to this semantic PS<->gold-mismatch leak; the adversarial
mismatch reconstruction above is the binding judgment, and it warrants the
relaxation rather than exclusion.

## Conclusion

No prescribed *code* fix exists for the leakage axis: the bundle cannot be made
both faithful and PS-only-non-leaking, because the public task text (proposing
to clip thresholds down to <= 1) and the gold fix (prepending `np.inf`, an
infinite leading threshold) are about *opposite* things. Per the relaxed-leakage
policy this instance is KEPT in the verified set: the verification core is sound
and the gold resolves, so `verify => correct` is unaffected; only the secondary
no-leakage property is relaxed for this documented instance.
