# refinement.md — django__django-14493

Maps every operation in `implementation_postProcess` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `postProcess` (`ManifestFilesMixin.post_process`)

Post-patch repo code (`patch.diff`), the relevant fragment:
```python
        paths = {path: paths[path] for path in adjustable_paths}
        substitutions = False                       # <-- the gold insertion

        for i in range(self.max_post_process_passes):
            substitutions = False
            for name, hashed_name, processed, subst in self._post_process(...):
                processed_adjustable_paths[name] = (name, hashed_name, processed)
                substitutions = substitutions or subst
            if not substitutions:
                break

        if substitutions:
            yield 'All', None, RuntimeError('Max post-process passes exceeded.')
```

Lean impl (`implementation_postProcess`): an `Id.run do` loop over
`List.range maxPasses` with a mutable `Option Bool` flag, overwritten each pass
with that pass's substitution outcome and an early `break` when a pass produces
none.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `maxPasses : Nat` | `self.max_post_process_passes : int` (≥ 0), the bound of `for i in range(...)` | **R** | `int ≥ 0` ↔ `Nat`; `range(self.max_post_process_passes)` ↔ `List.range maxPasses` (mapping.md bijection). |
| 2 | `passSubst : Nat → Bool` | pass `i`'s aggregated `substitutions = substitutions or subst` over `self._post_process(...)`, where the inner loop reinitializes `substitutions = False` at its top | **R** | the inner content-rewriting loop's pass-level outcome is a `bool` depending only on pass `i` (it is re-zeroed each pass), abstracted as `passSubst i` (mapping.md per-pass abstraction note). Not the changed op; the inner-loop body is unchanged by the patch. |
| 3 | `let mut substitutions : Option Bool := some false` | `substitutions = False` inserted before the loop (`patch.diff` added line) | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch initializes the flag to `False` before the loop; the model initializes the mutable flag to `some false`. The prepatch impl initializes it to `none` (the base_commit state — the variable is unbound until the loop body first assigns it). This is the single op the discriminating clause turns on. |
| 4 | `for i in List.range maxPasses do …` | `for i in range(self.max_post_process_passes):` | **I** | identical bounded iteration; `List.range maxPasses` enumerates `0..maxPasses-1` exactly as `range(...)`. |
| 5 | `substitutions := some (passSubst i)` | the inner loop, whose net effect each pass is to set `substitutions` to that pass's aggregated `or`-fold (`substitutions = False` then `substitutions = substitutions or subst` over the pass) | **I** | each pass overwrites the flag with its own outcome; the per-pass `or`-fold value is `passSubst i` (row 2). Boolean `b` ↔ `some b`. |
| 6 | `if ! (passSubst i) then break` | `if not substitutions: break` | **I** | identical early-termination guard: stop at the first pass producing no substitutions. `not` ↔ `!`. |
| 7 | `return substitutions` | the value `substitutions` holds at `if substitutions:` after the loop | **I** | the modeled result IS the post-loop flag state (mapping.md result-type note). `some b` = bound to `b`; `none` = unbound. |
| 8 | `Id.run do … : Option Bool` | the local `substitutions`'s runtime state (a `bool`, or unbound) | **R** | result modeled as `Option Bool`: a bound boolean is `some b`, the `UnboundLocalError` (referenced-before-assignment) state is `none`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch loop's flag outcome.

## Soundness check (verify ⟹ correct)

- `problem_spec_postProcess` pins the result to a *defined* `some _` whose value
  is the exact loop computation (`passLoopResult (List.range maxPasses) passSubst
  false`) for EVERY configuration (directive 5 — frame: the result is never left
  unconstrained, in particular it is fully pinned when `maxPasses = 0`;
  directive 8 — the value is grounded structurally in the inputs `maxPasses` and
  `passSubst` via the explicit fold, not an ungrounded oracle). A verifying impl
  must therefore (a) terminate the bounded loop with a *bound* flag for every
  configuration, and (b) compute that flag as the pass-by-pass overwrite with
  early break.
- The discriminating clause is definedness at `maxPasses = 0`: the spec demands
  `result = some (passLoopResult [] passSubst false) = some false`. The prepatch
  impl initializes the flag to `none` and, with a zero-trip loop, returns `none`
  — disagreeing with the spec. Hence the carried gold proof's `zero` case (which
  closes by `rfl` only when the impl returns `some false`) fails to typecheck
  against the prepatch impl (G-DIFF/G-PANEL). The `succ` case also fails, since
  the prepatch flag would still be `none` if pass 0 ran an inner loop with no
  files — but the `zero` case alone is the decisive, always-failing witness.
- This is exactly what the FAIL_TO_PASS test
  (`test_collectstatistic_no_post_process_replaced_paths`, a subclass with
  `max_post_process_passes = 0`) exercises: with zero passes the post-process
  must complete and report files as `post-processed`; pre-patch it raised
  `UnboundLocalError`.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  loop's flag outcome, over a grid of `maxPasses` ∈ 0..K × per-pass boolean
  patterns plus ≥1e5 fuzzed points (0 disagreements).
