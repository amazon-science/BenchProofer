# refinement.md — sympy__sympy-15875

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`sumIsZero` `do` block, the deep `classify`/`tallyAll`/`verdict` model, and the
`residualIsZero` opaque reference) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized/opaque callee —
**A-consumed** where the proof uses the contract's `ensures`, **A-reference**
where a deep model / opaque stand-in is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The decision site — `Add._eval_is_zero` (`sympy/core/add.py:532`)

Gold hunk (`add.py:557`):
```
         if z == len(self.args):
             return True
-        if len(nz) == len(self.args):
+        if len(nz) == 0 or len(nz) == len(self.args):
             return None
         b = self.func(*nz)
         if b.is_zero:
```

| # | Solution.lean impl op (`sumIsZero`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `isComm : Option Bool`, `args : List Term` | `self.is_commutative`, `self.args` | R | tri-state `is_X` ↔ `Option Bool`; tuple of summands ↔ `List Term` projected onto the four read facts (mapping.md §2). |
| A2 | the `while` fold building `acc = tallyAll args` via `classify` | the `for a in self.args:` accumulation loop (`add.py:539-553`) computing `z`, `nz`, `im`, `im_or_z`, and the bare `return` | R + I | the loop is a per-element fold; modeled as the backward `while` over the front-recursive `tallyAll`. Each branch of `classify` is the matching `if a.is_real / is_zero / is_imaginary / (I*a).is_real` cascade. The bare `return` (unclassifiable term) ↔ `bail`. Loop ops (`::`, index walk) are **I**; the fact reads are **R**. |
| A3 | `verdict isComm n acc`: the post-loop cascade `isComm=some false → none`; `bail → none`; `z = n → some true`; **`nz.length = 0 ∨ nz.length = n → none`**; else consult `residualIsZero nz` | the post-loop cascade (`add.py:554-566`): `is_commutative is False → return`; bare returns; `z == len → True`; **`len(nz) == 0 or len(nz) == len → None`**; else `b = self.func(*nz); b.is_zero …` | I + A-reference | the **changed** disjunct lives here, modeled **concretely**: `nz.length = 0 ∨ nz.length = n` is the exact post-patch guard `len(nz) == 0 or len(nz) == len(self.args)`. No axiom hides the change — it is a literal disjunction in `verdict`. The combine-with-imaginary-tallies tail (`!imOrZ && !im → some true`, `im && !imOrZ → some false`, else none) transliterates `add.py:558-563` literally (**I**). |
| A4 | `residualIsZero nz` — the zero-test of the residual real-nonzero sum | `b = self.func(*nz); b.is_zero` (`add.py:557,558,564`) | **A-reference** | the residual sub-decision is **unchanged** by the patch; modeled as the opaque `residualIsZero` (no asserted contract; proof consumes none). Validated **patch-invariant on the reached domain** by axiom_check.py (G-AX): pre/post-patch agree whenever `nz` is proper-nonempty. mapping.md §3. |
| A5 | result returned (`Option Bool`) | the function's `True`/`False`/`None` return | R | `Option Bool` ↔ tri-state (mapping.md §2). |

Discriminating content of the change — when **no** summand is real-and-definitely-
nonzero (`nz` empty) the verdict is **undetermined** (`None`), not a definite
value — lives in A3's disjunct `acc.nz.length = 0 ∨ …`. The issue's reproducer
`-2*I + (1+I)**2` is exactly this case: both summands are pure-imaginary, so
`nz = []`; pre-patch fell through to `b = self.func()` (empty residual) →
`b.is_zero = True` → combined to `return False`; post-patch returns `None`.
`Solution_prepatch.lean` reproduces the pre-patch cascade (the disjunct's
`nz.length = 0` half removed) and **fails** `out = sumIsZeroSpec isComm args` on
exactly the `verdict` clause (G-DIFF, verified: the unsolved goal is the
prepatch's `if … nz.length = args.length …` cascade `= verdict isComm args.length acc`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
short-circuit guard `len(nz) == 0 or …` — is modeled **concretely** as the
disjunction `acc.nz.length = 0 ∨ acc.nz.length = n` in `verdict` (step A3, an I
op), not hidden behind an axiom about the function under change. The only A leg is
`residualIsZero` (A4), which covers an **unchanged** recursive sub-decision and is
an **A-reference** (opaque, patch-invariance-validated by G-AX) with **no
consumed axiom**: the proof of `sumIsZero` discharges purely by the fold
(`loom_solve` + drop-step) and unfolding `verdict`/`sumIsZeroSpec`; it consumes no
`ensures` of `residualIsZero`.

## C. verify(Solution) ⇒ resolved

`sumIsZero` verifies only if its output equals `verdict isComm args.length
(tallyAll args)` — whose decisive clause `acc.nz.length = 0 ∨ acc.nz.length = n →
none` (A3) is precisely the post-patch guard. By R (`Option Bool ↔` tri-state,
`List Term ↔ self.args`) the verified verdict equals `Add._eval_is_zero(self)`'s
post-patch return for each input; by G-AX the opaque `residualIsZero` is the
unchanged `self.func(*nz).is_zero` (patch-invariant where reached, A-reference);
by G-CONF the R/I transliteration of the fold + cascade agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the one audited callee —
and the gold patch resolves (G-RESOLVE). The single trust point is residual-
sub-decision fidelity (G-AX); the refinement fidelity is this doc (G-EQ + G-CONF).
