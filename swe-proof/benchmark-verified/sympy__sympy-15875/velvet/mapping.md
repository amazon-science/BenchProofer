# mapping.md — sympy__sympy-15875

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b506169ad727ee39cb3d60c8b3ff5e315d443d8e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one opaque callee.

Repo file under change: `sympy/core/add.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `sumIsZero (isComm) (args)` | `Add._eval_is_zero(self)` — `sympy/core/add.py:532` | the modeled changed function (three-valued zero-test for a commutative sum) |
| `Term` (structure) | one element of `self.args` (a `sympy` `Expr`), projected onto the four fuzzy facts the method reads | the per-term observation carrier |
| `Term.isReal` | `a.is_real` | fuzzy fact read at `add.py:540` |
| `Term.isZero` | `a.is_zero` | fuzzy fact read at `add.py:541,543` |
| `Term.isImaginary` | `a.is_imaginary` | fuzzy fact read at `add.py:547` |
| `Term.iMulReal` | `(S.ImaginaryUnit*a).is_real` | fuzzy fact read at `add.py:549` |
| `isComm` (param) | `self.is_commutative` | fuzzy fact read at `add.py:533` |
| `classify` / `tallyAll` / `Tally` | the `for a in self.args` accumulation loop (`add.py:539-553`): `z`, `nz`, `im`, `im_or_z`, plus the early bare `return` (`bail`) | pure spec: the per-term tally fold |
| `verdict` | the post-loop decision cascade (`add.py:554-566`) | pure spec: tally → three-valued verdict |
| `residualIsZero (nz)` *(opaque — A-reference)* | `self.func(*nz).is_zero` — `b = self.func(*nz); if b.is_zero …` (`add.py:557-565`) | UNCHANGED residual sub-decision: the zero-test of the sum of the real-nonzero terms, deferred to recursively. Left opaque; patch-invariance validated by axiom_check.py (G-AX). |

The pre-patch behaviour the change fixes (refinement audit only, not in the
consumer spec view): when `nz` is **empty** (no real-and-definitely-nonzero
term), the pre-patch fell through to `b = self.func(*nz)` with an empty residual
and combined `b.is_zero` with the imaginary tallies, sometimes yielding a
definite `True`/`False`; the post-patch returns `None` (undetermined) in that
case.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo objects.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.args` (a tuple of `Expr` summands) | `List Term` | order-immaterial: every modeled fact is per-element and the verdict reads only counts / membership, so any tuple order maps to the same `List Term` verdict. `len(self.args)` ↔ `args.length`. |
| a single fuzzy fact `expr.is_X` (`True`/`False`/`None`) | `Option Bool` | `True ↔ some true`, `False ↔ some false`, `None ↔ none`. SymPy's three-valued assumption lattice is exactly `Option Bool`. |
| one summand `a`, as read by the method | `Term` with the four projected facts | `a ↦ { isReal := a.is_real, isZero := a.is_zero, isImaginary := a.is_imaginary, iMulReal := (S.ImaginaryUnit*a).is_real }` (each via the `Option Bool` bijection above). The method reads **only** these four facts of each summand. |
| `self.is_commutative` | `isComm : Option Bool` | the `Option Bool` bijection. |
| the method's return (`True`/`False`/`None`) | `out : Option Bool` | the `Option Bool` bijection. |

The method **mutates nothing** (`self`, `self.args`, and every summand are
read-only); `sumIsZero` declares no `mut` parameter and the spec frames the whole
output as `sumIsZeroSpec isComm args` — directive 5 is satisfied vacuously (no
mutable input frame to pin).

## 3. The opaque callee `residualIsZero` ↔ `self.func(*nz).is_zero` (A-reference)

**Callee:** the recursive zero-test `b.is_zero` where `b = self.func(*nz)` and
`nz` is the list of real-and-definitely-nonzero summands. This is an **unchanged**
sub-decision: it is computed over a *smaller, strictly-real* residual sum and the
patch does not touch how `b.is_zero` is computed. The change is purely a guard
**around** when this sub-decision is consulted — specifically, the patch adds an
early `len(nz) == 0` short-circuit to `None` *before* `b` is ever built. Whenever
the residual sub-decision IS still reached (i.e. `nz` proper-nonempty), the
pre-patch and post-patch compute the identical `self.func(*nz).is_zero`.

`residualIsZero` is therefore modeled as an **opaque** `List Term → Option Bool`
with **no asserted contract**; the proof of `sumIsZero` consumes no `ensures` of
it (it discharges purely by the fold + the `verdict` definition). It is an
**A-reference**, not an A-consumed axiom.

**Soundness check (G-AX), `axiom_check.py`:** runs the REAL `Add._eval_is_zero`
on the pre-patch and post-patch `add.py` over boundary + fuzzed unevaluated
`Add(*summands)` and asserts the single property the opaque modeling relies on —
**patch-invariance on the reached domain**: for every input where the residual
sub-decision is reached (`nz` proper-nonempty), pre-patch verdict == post-patch
verdict; and for every input the two verdicts differ ONLY when `nz` is empty
(the guarded case). This is exactly the claim that `residualIsZero` is an
unchanged callee the patch routes around, never a changed op. Imports only
`sympy`. Exit 0 iff sound.

### 3.1 Flag/branch coverage for the fuzzer
The four `Term` facts partition each summand into the branches `classify`
encodes. Representative atoms (used by both gates so every branch is exercised):

| branch | example summand `a` | `(isReal,isZero,isImaginary,iMulReal)` |
|---|---|---|
| real & zero (`z`) | `Integer(0)` | `(T,T,F,T)` |
| real & nonzero (`nz`) | `Symbol(real=True,nonzero=True)`, `Integer(2)`, `sqrt(2)` | `(T,F,F,F)` |
| real, zero undetermined (`bail`) | `Symbol(real=True)` | `(T,N,F,N)` |
| pure imaginary (`im`) | `I`, `2*I`, `(1+I)**2`, `Symbol(imaginary=True)` | `(F,F,T,T)` |
| imaginary-or-zero (`imOrZ`) | `I*Symbol(real=True)` | `(N,N,N,T)` |
| unclassifiable (`bail`) | `Symbol()` (generic) | `(N,N,N,N)` |

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15875`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`classify`/`tallyAll`/`verdict` (R/I-tagged ops) to Python and leaves the
A-tagged residual sub-decision as the **real** `self.func(*nz).is_zero` (run the
real callee, not the opaque model), exactly as the gold patch computes it.
