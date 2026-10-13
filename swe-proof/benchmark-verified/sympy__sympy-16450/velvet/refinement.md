# refinement.md — sympy__sympy-16450

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `makeSurrogates` `do` block, the deep `surrogate`/`surrogatesAll` model, and
the `closeProps` deep-model reference) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized/uninterpreted
callee — **A-consumed** where the proof uses the contract's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The replacement-construction site — `posify()` (`sympy/simplify/simplify.py:254`)

Gold hunk:
```
- reps = {s: Dummy(s.name, positive=True)
+ reps = {s: Dummy(s.name, positive=True, **s.assumptions0)
              for s in eq.free_symbols if s.is_positive is None}
  eq = eq.subs(reps)
  return eq, {r: s for s, r in reps.items()}
```

| # | Solution.lean impl op (`makeSurrogates`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `symbols : List Sym` | `eq.free_symbols` (a `set` of `Symbol`) | R | a set of symbols ↔ `List Sym`; the modeled property is per-element so any order is faithful (mapping.md §2). G-CONF bridges via the field projection `s ↦ (s.assumptions0, s.is_positive)`. |
| A2 | the `while` fold over `symbols`, prepending `surrogate s` | the dict comprehension `{s: Dummy(...) for s in eq.free_symbols if s.is_positive is None}` then `eq.subs(reps)` read back through each surrogate's `assumptions0` | R + I | the comprehension is a per-element map; modeled as the front-recursive fold. The observable is each surrogate's resolved fact set, in order; `subs`/dict identity is the R-abstraction (mapping.md §2). The loop ops (`::`, the index walk) are **I**. |
| A3 | the `if s.sign = none` guard | the comprehension filter `if s.is_positive is None` | I | `s.sign = none` ↔ `s.is_positive is None` under the `Option Bool` bijection (mapping.md §2). A determined-sign symbol is not replaced (left as `s.props`). |
| A4 | `("positive", true) :: s.props` — the **argument** handed to the closure engine for an under-determined symbol | `positive=True, **s.assumptions0` — the kwargs handed to `Dummy(...)` | **I** | the changed operation, modeled **concretely**: assert positivity *prepended to* the symbol's already-declared facts. This is the whole patch: gold adds `**s.assumptions0`; the prepatch omits it. No axiom hides this — it is a literal cons. |
| A5 | `closeProps (…)` — close that fact-set to the full derived set | the closure performed inside `Dummy.__new__` → `StdFactKB(...)`, observed via `.assumptions0` | **A-reference** | the closure engine is **unchanged** by the patch; modeled as the uninterpreted `closeProps`. Validated `closeProps == real Dummy(...).assumptions0` by axiom_check.py (G-AX). NOT a consumed axiom — the proof uses no `ensures` of it. mapping.md §3.1. |

Discriminating content of the change — a declared property such as
`finite=True` on a sign-undetermined symbol is **preserved** in the surrogate —
lives in A4: `surrogate s = closeProps (("positive", true) :: s.props)` (model)
⇔ `Dummy(s.name, positive=True, **s.assumptions0).assumptions0` (real). The
pre-patch built `Dummy(s.name, positive=True)`, i.e. `closeProps [("positive",
true)]`, which drops `s.props`; `Solution_prepatch.lean` reproduces exactly that
and **fails** `out = surrogatesAll symbols` on the A4 clause (G-DIFF, verified:
the unsolved goal is `closeProps [("positive", true)] = surrogate s`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
argument given to the symbol constructor — is modeled **concretely** as the cons
`("positive", true) :: s.props` (step A4, an I op), not hidden behind an axiom
about the function under change. The only A leg is `closeProps` (A5), which
covers an **unchanged** callee (the assumption-closure engine) and is an
A-reference (deep-model-validated by G-AX), with **no consumed axiom**: the proof
of `makeSurrogates` discharges purely by the fold (`loom_solve` + drop-step), it
consumes no `ensures` of `closeProps`.

## C. verify(Solution) ⇒ resolved

`makeSurrogates` verifies only if its output equals, per element, `surrogate s`
— which for a sign-undetermined symbol is `closeProps (("positive", true) ::
s.props)`, i.e. positivity asserted **on top of** the symbol's declared facts
(A4). By R (`set ↔ List`, `Option Bool ↔ tri-state`, `subs`/dict identities) the
verified construction equals `Dummy(s.name, positive=True, **s.assumptions0)` for
each replaced symbol; by G-AX the deep model `closeProps` equals the real
`StdFactKB` closure read through `assumptions0` (A-reference); by G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). The single trust point is closure-engine fidelity (G-AX);
the refinement fidelity is this doc (G-EQ + G-CONF).
