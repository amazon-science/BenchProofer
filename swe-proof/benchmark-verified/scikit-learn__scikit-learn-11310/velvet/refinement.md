# refinement.md — scikit-learn__scikit-learn-11310

Maps every op in `Solution.lean`'s `do` block (`recordRefitTime`) to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's contract), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R / A / I. No kind-3
(changed-inexpressible) op.

The two `time.time()` readings are environment-provided values of an unchanged
callee. They enter the method as the read-only inputs `startT` / `endT`, with
the monotone-clock contract stated as the precondition `require startT ≤ endT`
(mapping.md §3, validated by G-AX). The postcondition pins the recorded value
to exactly `some (endT - startT)` — the identical subtraction the patched
source performs — so the impl cannot substitute a constant or any other value
(spec-strength repair, 2026-08-05; see mapping.md §2).

## Correspondence table

| # | `Solution.lean` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if refit then … else …` | `if self.refit:` (`_search.py:766`, pre-existing gate kept by the patch) | **R** | `refit : Bool` ⇔ truthiness of `self.refit`. Both sides record the duration only under the truthy gate. The gate is unchanged by the patch; modeling it is required to express "recorded only when refitting." |
| 2 | input `startT` (+ `require startT ≤ endT`) | `refit_start_time = time.time()` (added line) | **A-consumed** | `time.time()` is an UNCHANGED callee (the patch only `import time`s and calls it). Its first reading is environment-provided — modeled as the read-only input `startT`. The axiom (non-decrease vs the later reading) is the `require startT ≤ endT` precondition, consumed by the proof of `t ≥ 0`. G-AX validates against the real `time.time()`. |
| 3 | input `endT` (+ `require startT ≤ endT`) | `refit_end_time = time.time()` (added line), taken AFTER `best_estimator_.fit(...)` | **A-consumed** | The second reading, constrained to be `≥` the first by the same precondition: the monotone-clock contract (mapping.md §3). This is the load-bearing axiom — the proof of non-negativity consumes exactly `startT ≤ endT`. G-AX reads the real clock twice in succession and asserts non-decrease. |
| 4 | `refitTime := some (endT - startT)` | `self.refit_time_ = refit_end_time - refit_start_time` (added line) | **R** | `refitTime : Option Rat` ⇔ the instance attribute `self.refit_time_` (`none` ⇔ absent / `hasattr` False; `some t` ⇔ present with value `t`). `endT - startT : Rat` ⇔ the float subtraction `refit_end_time - refit_start_time`. The postcondition pins this assignment EXACTLY (`ensures refit = true → refitTime = some (endT - startT)`). The R leg (the subtraction) is G-CONF differential-tested bit-exact against this verbatim patch line. |
| 5 | `else: return ()` (slot left `none`) | (no `else` branch; `self.refit_time_` simply never assigned when `self.refit` is falsy) | **I** | Identical no-op: under the falsy gate neither side records anything, so the attribute stays absent. Pinned exactly by `ensures refit = false → refitTime = none` (directive 5). |

## Elided (not a do-block op, not an axiom — documented)

The intervening `best_estimator_.fit(X, y, …)` / `.fit(X, …)` call (`_search.py:769–772`)
is the work being timed. It is **unchanged** repo code; the patch does not touch
it. Its only effect on the modeled property is to advance the wall clock between
readings 2 and 3 — already captured by the `startT ≤ endT` precondition. It pins
no observable that the spec constrains, so it is intentionally elided rather than
axiomatized (avoiding a dead axiom per SPEC_GUIDE §3 / directive 7). The `clone(...).set_params(...)`
that builds `best_estimator_` (`_search.py:767–768`) is likewise unchanged and
unobservable through the spec; elided.

## Self-audit

- Every do-block op is tagged R / A-consumed / I. No A-reference (no changed op
  is deeply re-implemented; the only callee, `time.time()`, is consumed as an
  axiom/precondition, not re-modeled).
- No kind-3 op: the changed behavior (bracket-and-record) is fully expressible.
- A-consumed axiom (monotone clock, `require startT ≤ endT`) is about an
  unchanged callee, is the weakest contract sufficient
  (`startT ≤ endT ⊢ endT - startT ≥ 0`), and is G-AX executable-checkable.
  It is NOT the function under spec and NOT the changed op.
- Directive 8 (grounding): the recorded value is pinned to the arithmetic
  relation `some (endT - startT)` on the actual input carrier — no ungrounded
  oracle; a wrong impl cannot echo it without performing the subtraction of the
  two readings, and constant-recording impls fail on any pair with a different
  difference.
- R legs (steps 1, 4) are mechanically refuted by `conformance_check.py` (G-CONF).
