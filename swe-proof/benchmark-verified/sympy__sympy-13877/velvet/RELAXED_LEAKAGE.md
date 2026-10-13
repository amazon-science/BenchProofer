# RELAXED_LEAKAGE — sympy__sympy-13877 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by this bundle's own recorded P2 audit
(`verdict.md`, DEFECT-1): "the no-leakage property (judged
problem_statement-only) cannot hold for any faithful spec — this is a
**RELAXED** leakage instance, not the clean NO-LEAKAGE that `meta.json
gates.G-LEAK.status` and the missing `RELAXED_LEAKAGE.md` currently claim.
… *Precise fix:* re-disposition `gates.G-LEAK.status` to `"relaxed"`, add an
in-bundle `RELAXED_LEAKAGE.md` … Core soundness is unaffected." The
subsequent re-audit's G-PANEL-3 LEAKAGE verdict found the identical facet
(same two leaking lines, same token-scan evidence) against the bundle that
still lacked this disposition. This file implements the prescribed fix.

## The mismatch

The gold fix to the Bareiss determinant
(`sympy/matrices/matrices.py`, `_eval_det_bareiss`) replaces the inner
pivot finder

```
def _find_pivot(l):
    for pos,val in enumerate(l):
        if val:                      # structural truthiness
            return (pos, val, None, None)
    return (None, None, None, None)
```

with

```
pivot_pos, pivot_val, _, _ = _find_reasonable_pivot(mat[:, 0],
                             iszerofunc=_is_zero_after_expand_mul)
```

plus the new module helper `_is_zero_after_expand_mul(x) = (expand_mul(x) == 0)`.
The discriminator is the zero-test that decides pivot selection: structural
truthiness (`bool(x)`) → algebraic zero after normalisation
(`expand_mul(x) != 0`).

- **Public `problem_statement`:** ONLY the crash reproduction
  (`M(n) = Matrix([[i + a*j] …])`, `det(M(5))` → `nan`, `det(M(6))` →
  `Invalid NaN comparison` traceback) and the reporter's INCORRECT hypothesis
  ("Is the Bareiss algorithm only valid for integer matrices?"). Token scan
  (recorded twice, at construction audit and at the re-audit): zero/nonzero/
  expand/expand_mul/normalis/iszero/select/pivot-fix vocabulary = **0
  occurrences** in problem_statement.
- **The fix vocabulary lives only in the EXCLUDED `hints_text`** ("some zero
  detection like `val = val.expand()` before `if val:`") and in the gold
  diff itself.

The leaking lines are the spec view's `Entry`/method docstrings:

> "`mathNonzero` — the decisive recogniser: the value is still non-zero after
> algebraic normalisation. This is the observation that decides selection."

> "The decision must rest on the decisive recogniser alone — an entry that
> merely looks non-zero but normalises to zero must be skipped."

together with the discriminating postcondition clause
`res.found = true → (col[res.idx]!).mathNonzero = true`.

## Why the leak is unavoidable

Faithfulness forces the structural-vs-algebraic distinction into the spec:

- The prepatch bug IS "select on structural truthiness"; the gold behavior
  IS "select on algebraic non-zero after expand_mul". Any spec that rejects
  the prepatch bug (G-DIFF: `Solution_prepatch.lean`, which scans on
  `litNonzero`, must fail) while accepting the gold behavior MUST contain a
  clause that distinguishes the two recognisers on entries where they
  disagree (structurally non-zero yet algebraically zero — exactly the
  issue's `a*(a-1) - a*a + a` pattern). That clause is the gold
  discriminator, verbatim.
- A spec derivable from the problem_statement alone (traceback + wrong
  integer-matrices hypothesis) cannot pin the selection to the decisive
  recogniser — it would admit the prepatch scan, a spec-too-weak (G-EQ P1)
  defect, or pin some unrelated non-faithful behavior (e.g. "restrict
  Bareiss to integer matrices", which the gold patch does NOT do).
- Faithful + non-leaking is therefore provably impossible here; both the
  construction audit (verdict.md sub-review 3: "VERDICT: RELAXED … it is
  unavoidable under faithfulness") and the re-audit (same two leaking lines,
  same token scan) derived exactly this shape.

This is the same faithful-must-leak shape as the dispositioned
django__django-13023 instance (ValueError-membership facet): the
discriminator exists only in gold + hints_text, and the spec cannot be both
faithful and silent about it.

## Core soundness is intact (per the recorded P2 audit + re-audit)

- G-VERIFY: Solution.lean verifies; proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (litNonzero scan — the prepatch `if val:`)
  fails for the right reason: the discriminating clause
  `res.found = true → (col[res.idx]!).mathNonzero = true`.
- G-EQ / G-PANEL-1: spec-too-weak attacks (incl. the byte-identical prepatch
  bug, echo, wrong-index, out-of-bounds variants) rejected, each on a
  specific postcondition clause; positive control (structurally different
  correct impl) verifies. (The partial-correctness divergence hole the
  re-audit found is fixed separately: the spec now runs under
  `loom.semantics.termination "total"` with a `decreasing` measure, so a
  non-terminating impl no longer verifies.)
- G-PANEL-2 (faithfulness): FAITHFUL — model output == real post-gold
  `_find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul)` on
  every F2P pivot call (0 mismatches) and on independent fuzz (20000
  columns, 0 divergences).
- G-CONF: 0 / 100008 disagreements (seed 13877). G-AX: sound on 19 boundary
  + 12002 fuzz scalars; `_find_reasonable_pivot` agreement on 306 columns.
  G-MUT: 19/20 killed (survivor benign: dead-store initial `idx`).
  G-RESOLVE: resolved (gold verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the structural-truthiness → algebraic-zero pivot-test discriminator).
