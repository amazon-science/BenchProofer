# refinement.md — scikit-learn__scikit-learn-13779

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`validateWeightSupport` `do` block and the deep `validate` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The validation site — `_BaseVoting.fit` (`sklearn/ensemble/voting.py:76-81`)

Gold hunk:
```
 if sample_weight is not None:
     for name, step in self.estimators:
+        if step is None:
+            continue
         if not has_fit_parameter(step, 'sample_weight'):
             raise ValueError('Underlying estimator \'%s\' does not'
                              ' support sample weights.' % name)
```

| # | Solution.lean impl op (`validateWeightSupport`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `members : List Member` | `self.estimators` (list of `(name, step)`) iterated by the `for` loop | R | list-of-pairs ↔ `List Member`; order preserved (mapping.md §2). G-CONF bridges via the per-member kind coding. |
| A2 | the method runs under the gate that a per-sample weighting is supplied | the enclosing `if sample_weight is not None:` | R | the gate is the condition under which this scan is `fit`'s behavior; `validateWeightSupport` models the already-gated scan (mapping.md §2). |
| A3 | per-member guard `m.present && !m.supports` | `if step is None: continue` (skip absent) **followed by** `if not has_fit_parameter(step, 'sample_weight'):` (the present-unsupported test) | R + I | `step is None` ↔ `present = false` and `has_fit_parameter(step,'sample_weight')` ↔ `supports` (mapping.md §2, R). The conjunction `present && !supports` is the I-transliteration of "skip-if-absent, then raise-if-unsupported": an absent member fails the `present` conjunct (skipped, the FIX); a present unsupported member satisfies both (raises). The boolean predicate `has_fit_parameter` is consumed as an input bit, **not** axiomatized (mapping.md §3 — no consumed axiom). |
| A4 | error leg `Except.error m.name` at the first satisfying member; the backward `while` fold keeps the front-most failure | `raise ValueError('Underlying estimator \'%s\' ... ' % name)` at the first offending member (the `for` loop raises and unwinds, so the first one wins) | R + I | the raise's only observable (F2P/P2P `assert_raise_message`) is "raises naming this member"; modeled as `Except.error name` (R). "First in order wins" is I: the gold `for` raises on the first match; the spec's `validate` returns the first guarded `Except.error` (front-recursive), and the backward loop preserves the front-most one. |
| A5 | success leg `Except.ok ()` when no present member is unsupported | the loop falls through; `fit` proceeds | R | fall-through ↔ `Except.ok ()` (mapping.md §2). |

Discriminating content of the change — an **absent** member (`step is None`,
`present = false`) must be **skipped**, not treated as unsupported — lives in the
`m.present` conjunct of A3. `Solution_prepatch.lean` drops that conjunct (guard
`!m.supports` only), so an absent member wrongly takes the error leg; it
**fails** `out = validate members` (G-DIFF) on exactly any input containing an
absent member ahead of (or instead of) a clean scan.

## B. No axioms, no deep-model reference

There is **no consumed axiom** and **no A-reference callee model** in this
bundle (mapping.md §3). The one repo callee the scan invokes,
`has_fit_parameter(step, 'sample_weight')`, is a pure boolean predicate whose
verdict is carried as the input bit `Member.supports` — a **type refinement** of
the member carrier (R, row A3), not an axiomatized contract. The spec asserts
nothing about *how* `has_fit_parameter` decides; it consumes the verdict. The R
refinement's faithfulness (supported ↔ True, unsupported ↔ False, `None` ↔
absent) is bridge-checked by `axiom_check.py` and refuted end-to-end by G-CONF.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — skipping an
absent member before the support check — is modeled **directly** as the
`m.present` conjunct of the guard (A3, R+I), not hidden behind an axiom. There
is no consumed axiom and no A-reference; nothing inexpressible.

## D. verify(Solution) ⇒ resolved

`validateWeightSupport` verifies only if its output equals `validate members`:
absent members skipped (A3 `present` conjunct), the first present-unsupported
member reported on the error leg (A4), success otherwise (A5). By R
(`self.estimators ↔ List Member`, `step is None ↔ present=false`,
`has_fit_parameter ↔ supports`, raise-with-label ↔ `Except.error name`,
fall-through ↔ `Except.ok ()`) the verified scan equals the gold patched
validation block on the tested ensembles; by G-CONF the R/I transliteration of
`validate` agrees with `patch.diff`'s real `fit` behaviour (raise-or-not, and
the offending label) on ≥10⁵ fuzzed ensembles. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The trust point is exactly refinement
fidelity (this doc, G-EQ + G-CONF); there are no axiom trust points (no
consumed axioms).
