# RELAXED_LEAKAGE — scikit-learn__scikit-learn-26194 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). This file supplies the
in-bundle documentation the bundle's P2 audit (verdict.md, sub-review 3 —
verdict RELAXED) found missing: the leak was judged genuine but provably
unavoidable, and the recommended fix was exactly this disposition record.

## The mismatch (problem_statement ↔ gold)

The gold patch (`sklearn/metrics/_ranking.py`, `roc_curve`) replaces the
anchoring lead of the returned `thresholds` vector:

```
- thresholds = np.r_[thresholds[0] + 1, thresholds]
+ thresholds = np.r_[np.inf, thresholds]
```

Its discriminating behavioral content: the leading ("no instance predicted
positive") threshold is **positive infinity** — a value categorically above
every attainable finite score — not any finite number.

That content is not derivable from the public `problem_statement`. The PS:

- reports only the *symptom* ("Thresholds can exceed 1 in `roc_curve` while
  providing probability estimate") with a non-regression test asserting the
  tautology `np.logical_or(thresholds <= 1, thresholds >= 0).all()`;
- proposes the **OPPOSITE** remedy: "A potential workaround would be to check
  `thresholds.max() <= 1` in which case we should clip `thresholds` to not be
  above 1" — i.e. a finite cap ≤ 1;
- never mentions infinity. Token scan of the frozen `instance.json`:
  `inf` / `isinf` / `np.inf` / `infinit` / `sentinel` all have 0 hits in
  `problem_statement`; `hints_text` is the empty string. These tokens live
  only in the gold patch and `test_patch`. (Re-confirmed by the P2 audit,
  verdict.md sub-review 3.)

## The leak (what the spec view discloses beyond the PS)

The spec view necessarily encodes the infinite-sentinel discriminator:

- the `Threshold` inductive's docstring: "`top` is the sentinel position that
  classifies NO instance as positive — it sits strictly above every attainable
  finite score, so the curve is anchored at the (0,0) corner";
- the `withLeadingSentinel` docstring: "the result is `base` … preceded by the
  sentinel that lies above every finite threshold";
- the postcondition `ensures out = Threshold.top :: finiteSeq base`.

Under the bundle's own bijection (mapping.md §2: `np.inf ↔ Threshold.top`)
this reconstructs the gold edit `thresholds = np.r_[np.inf, thresholds]`
exactly. The leak is SEMANTIC (the pinned behavior IS the discriminator); it
is not a lexical repo-symbol or diff-line echo — the mechanical G-LEAK screen
passes ("spec view clean"), and no gold token appears in the spec view.

## Why the leak is unavoidable (faithful ⟹ leaking)

The frozen spec must pin the gold's F2P-tested behavior:

- `test_roc_curve_drop_intermediate` asserts thresholds `[np.inf, 1.0, 0.7,
  0.0]` and `[np.inf, 1.0, 0.9, 0.7, 0.6, 0.0]` — the lead is `np.inf`, and
  the tail is the finite thresholds unchanged;
- `test_roc_curve_with_probablity_estimates[42]` asserts
  `np.isinf(thresholds[0])` — exactly `out.head? = some Threshold.top`.

A solver faithful to the PS clips to ≤ 1 (a finite lead) and **fails** both
F2P tests: a finite lead is `Threshold.value _ ≠ Threshold.top`. Any spec
weak enough to HIDE the sentinel (e.g. only "lead ≥ every element" or "lead
≤ 1 for probability inputs") would admit exactly that PS-faithful clip
implementation — which G-DIFF requires to fail and which fails the hidden
F2P tests. So a spec faithful to the gold MUST pin "the lead lies above every
attainable finite score" (= the infinite sentinel); PS-only + faithful is
impossible (the PS's own proposed fix contradicts the gold). This is a proven
PS ↔ gold mismatch, not lazy de-narration: the leak survives full
de-narration because it lives in the postcondition's discriminating clause
(`out.head = Threshold.top`), not in prose — the spec-view docstrings already
avoid `np.inf`, `roc_curve`, and every repo symbol, stating only the abstract
sentinel property, which is the minimum-necessary disclosure.

## Core soundness (relaxation criteria 1–2, per the P2 audit / gate records)

- **G-VERIFY pass.** `Solution.lean` verifies (exit 0, 2.8 s), non-trivial
  exact-equality ensures.
- **G-DIFF fail (right clause).** `Solution_prepatch.lean` (finite lead
  `Threshold.value (base.head! + 1)`) fails `prove_correct` on exactly the
  discriminating head clause `value (base.head! + 1) ≠ top` — the precise
  `np.isinf(thresholds[0])` discriminator the F2P tests observe.
- **G-CONF pass.** R/I shadow `[np.inf, *base]` agrees with the real patched
  `roc_curve` thresholds on 100 007 fuzzed inputs (seed 26194),
  0 disagreements; without the gold patch the shadow disagrees with the
  unpatched oracle (`[max+1, …]`), so the check genuinely discriminates.
- **G-AX pass.** Real `_binary_clf_curve`(+drop) yields a non-empty,
  all-finite `base` on 20 013 inputs — `require base ≠ []` and the finite-Rat
  carrier are sound; no Lean axioms exist to over-claim.
- **G-EQ SOUND + TIGHT.** Single exact-equality postcondition pins a unique
  output per input; 7 spec-too-weak attacks (incl. the prepatch bug) all
  share the spec and all fail to verify; positive control verifies; all
  refinement rows R/I, no kind-3 holes.
- **G-PANEL-2 FAITHFUL.** Spec mirrors gold `np.r_[np.inf, thresholds]`;
  matches the F2P fixtures bit-for-bit on finite parts, and
  `isinf(thr[0]) ↔ out.head = top`; 200 k-input differential probe,
  0 divergences.
- **G-RESOLVE resolved.**

Criteria 1 (core sound) and 2 (leak genuinely unavoidable) hold; this file +
the `relaxed_leakage` meta flag supply criterion 3 (in-bundle documentation),
which the original bundle omitted (verdict.md, non-blocking defect #1).
