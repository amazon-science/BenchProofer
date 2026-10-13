# refinement.md — django__django-14493

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `passBudgetExceeded` `do` block plus the pure `overBudget`/`settledThrough`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The bounded-pass summary — `post_process` (`django/contrib/staticfiles/storage.py:248-256`)

Gold hunk:
```
         paths = {path: paths[path] for path in adjustable_paths}
+        substitutions = False
 
         for i in range(self.max_post_process_passes):
             substitutions = False
```

The fix initializes `substitutions = False` before the `for i in
range(self.max_post_process_passes):` loop, so the trailing read `if
substitutions:` (`storage.py:256`) is always bound — in particular when
`max_post_process_passes == 0` and the loop body never runs.

| # | Solution.lean impl op (`passBudgetExceeded`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `limit : Nat` | `self.max_post_process_passes : int >= 0` | R | non-negative `int` ↔ `Nat` (mapping.md §2). `range(limit)` ↔ loop while `i < limit`. |
| A2 | parameter `flags : List Bool` | the per-pass `subst` outcomes of `self._post_process` aggregated into the local `substitutions` (`storage.py:262`) | R | each `flags[i]!` ↔ "pass `i` reported a substitution". `_post_process` is unchanged by the patch; its outcomes are abstracted into `flags` (mapping.md §3). |
| A3 | `let mut exhausted := false` (the pre-loop initializer) | the **added** line `substitutions = False` | I | this IS the gold-patch line, transliterated: the summary flag is pinned to `false` before the bounded loop, so the zero-budget read is defined. |
| A4 | `while i < limit ∧ (i = 0 ∨ flags[i-1]! = true)` | `for i in range(self.max_post_process_passes):` with `if not substitutions: break` (`storage.py:266`) | R + I | the bounded `range` loop ↔ `i < limit`; the early stop `if not substitutions: break` ↔ the guard conjunct `(i = 0 ∨ flags[i-1]! = true)` (continue only while the previous pass still changed). |
| A5 | `exhausted := flags[i]!` (loop body) | `substitutions = substitutions or subst` collapsed under the per-pass model: after a full pass the summary equals that pass's `subst` | I | the loop body overwrites the summary with the current pass's change flag; faithful because the only way to reach pass `i+1` is `flags[i]! = true` (A4 guard), so `substitutions or subst == subst` at the relevant points. |
| A6 | `return exhausted`, `ensures out = overBudget flags limit` | the final `if substitutions:` test (`storage.py:256`) deciding whether to `yield 'All', None, RuntimeError('Max post-process passes exceeded.')` | I | `out` is exactly the post-loop value of `substitutions`. `overBudget flags limit = (0 < limit) && (all passes < limit changed)`: true iff the budget ran out while still changing; false when `limit = 0` (the fix). |

Discriminating content of the change — the zero-budget case `limit = 0` must
report `false`, not a stale/unbound value — lives in `overBudget flags 0 =
false` (model: `decide (0 < 0) && _ = false`) ⇔ the patched `substitutions =
False` being the value read at `storage.py:256` when the loop never runs.
`Solution_prepatch.lean` models the missing initializer (the summary left at the
unconstrained pre-loop value `true`) and **fails** `out = overBudget flags
limit` precisely on the `limit = 0` exit clause (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — pinning the
summary flag before the bounded loop — is modeled **concretely** (the
`let mut exhausted := false` initializer and the verified loop ARE the
computation). There is **no axiom** and **no deep-model reference**: the only
repo callee touched by the loop, `self._post_process`, is unchanged by the patch
and is abstracted into the input `flags` (mapping.md §3), not modeled.

## C. verify(Solution) ⇒ resolved

`passBudgetExceeded` verifies only if its output equals `overBudget flags limit`
— in particular `false` whenever `limit = 0` (A6), the exact behavior the
zero-budget F2P test
(`test_collectstatistic_no_post_process_replaced_paths`) demands: with
`max_post_process_passes = 0`, `post_process` must run to completion (no
`UnboundLocalError`) and report files post-processed. By R (`int ↔ Nat`,
`subst-sequence ↔ List Bool`) the verified loop equals the patched
`post_process` summary computation on the modeled inputs; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (including
the `limit = 0` boundary). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there are no axioms to trust (G-AX is degenerate, §3 of
mapping.md).
