# refinement.md — sympy__sympy-13974

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`distributePow` and `simplifyFactor` `do` blocks plus the deep
`powAll`/`factorImage`/`powF` model) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`ensures`), or **I** (identical concrete op).

**TWO modeled sites, both required.** The gold patch changes the handling of a
power-of-aggregate at TWO places: where such a power is the WHOLE expression
(§A) and where it occupies ONE FACTOR POSITION of a product (§A.2). An earlier
revision of this document modeled only §A and asserted in §B that the
factor-position handling "is not a new behavior". That assertion was FALSE and is
corrected below: pre-patch, `tensor_product_simp_Mul` returned the product
unchanged whenever it had a single non-commutative factor, and raised `TypeError`
when a non-`TensorProduct` factor came first, so a power-of-aggregate factor was
never routed to the per-position raise from any factor position. The consequence
was measured rather than argued — see §B.

**No axioms / no G-AX in this bundle.** The gold patch *adds* a helper
(`tensor_product_simp_Pow`); there is no UNCHANGED external callee to axiomatize.
The only callee — the `Pow` constructor `**`, modeled opaquely as `powF` — is run
for real on **both** sides of G-CONF, so it is an **I-leg** primitive. The deep
model's fidelity to the gold patch is therefore validated by **G-CONF on the
patched tree**, not by an A-reference under G-AX. (Putting it under G-AX would
violate directive 7 — validating the function under change — and would crash, as
the added function does not exist at `base_commit` where G-AX runs.)

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviorally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (byte-identical; G-RESOLVE).

## A. The new evaluation site — `tensor_product_simp_Pow`

Gold introduces, and routes `tensor_product_simp`'s `Pow` branch into, the
distribution of an exponent across an aggregate's factors:

```
- return tensor_product_simp(e.base) ** e.exp                 # exponent left on the aggregate
+ if isinstance(e.base, TensorProduct):
+     return tensor_product_simp_Pow(e)                        # TensorProduct(*[ b**e.exp for b in e.base.args])
+ else:
+     return tensor_product_simp(e.base) ** e.exp
```

| # | Solution.lean impl op (`distributePow`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `factors : List Factor` | `e.base.args` — the factor tuple of the aggregate | R | tuple ↔ `List Factor`, positional (mapping.md §2). G-CONF bridges element-wise. |
| A2 | parameter `n : Factor` | `e.exp` — the shared exponent | R | exponent ↔ `n`, held fixed across positions (mapping.md §2). |
| A3 | result is `powAll n factors`: position-wise `powF · n` over the sequence, computed by the backward `while` fold | `[ b**e.exp for b in e.base.args ]` then `TensorProduct(*...)` | I | the changed op is modeled **deeply**: `powAll`/`powF` (pure region) and the verified loop ARE the per-position raise. No consumed axiom. The fold ops (`powF b n`, `::`, the loop) are **I** (concrete; the per-factor `**` runs for real on both sides of G-CONF). The equality of that deep model to the real `tensor_product_simp_Pow` is validated mechanically by **G-CONF** on the patched tree (mapping.md §3.1) — there is no G-AX A-reference, because `tensor_product_simp_Pow` is the function under change and absent at base_commit. |
| A4 | `result` returned (`List Factor`) | `TensorProduct(*new_args)` rebuilt | R | aggregate reconstruction is the inverse of A1: same arity, same order (mapping.md §2). `tensor_product_simp` compares rendered factors. |

Discriminating content of the change — each factor `aᵢ` becomes `aᵢ ** n`, the
sequence's arity and order preserved — lives in `out = powAll n factors`
(model) ⇔ `TensorProduct(*[ b**e.exp for b in e.base.args])` (real). The pre-patch
branch returned `tensor_product_simp(e.base) ** e.exp`, leaving the factor
sequence UNCHANGED (exponent on the aggregate as a whole);
`Solution_prepatch.lean` reproduces that (`result := b :: result`, the bare
factor) and **fails** `out = powAll n factors` on the clause
`factors[i-1]! = powF factors[i-1]! n` (G-DIFF).

## A.2 The second changed site — factor-position routing inside `tensor_product_simp_Mul`

Gold also changes what happens when a power-of-aggregate occupies ONE FACTOR
POSITION of a product. Pre-patch, `tensor_product_simp_Mul` could not reach a
per-position raise from any factor position at all:

```
  if n_nc == 0 or n_nc == 1:
      return e                              # a lone nc factor: returned UNCHANGED
  ...
  if not isinstance(current, TensorProduct):
      raise TypeError('TensorProduct expected, got: %r' % current)   # a Pow factor: TypeError
```

Gold replaces each of those with a routing decision on the examined factor:

```
+ elif n_nc == 1:
+     if isinstance(nc_part[0], Pow):
+         return  Mul(*c_part) * tensor_product_simp_Pow(nc_part[0])
+     return e
+ if isinstance(current, Pow):
+     if isinstance(current.base, TensorProduct):
+         current = tensor_product_simp_Pow(current)      # leading position
+ if isinstance(next, Pow):
+     if isinstance(next.base, TensorProduct):
+         new_tp = tensor_product_simp_Pow(next)          # trailing position
+ elif e.has(Pow):
+     new_args = [ tensor_product_simp_Pow(nc) for nc in nc_part ]
```

All four spellings compute the same thing about the examined factor: **if it is a
power of an aggregate, its image is that aggregate's positions each raised to the
exponent; otherwise its image is its own positions, untouched.** That common
decision — and only it — is contracted by `simplifyFactor`.

| # | Solution.lean impl op (`simplifyFactor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A2.1 | parameter `isPowOfAggregate : Bool` | the routing test `isinstance(f, Pow) and isinstance(f.base, TensorProduct)` on the examined factor | R | boolean ↔ boolean (mapping.md §2, `isPowOfAggregate` row). No other repo state feeds the decision, so the refinement is a plain bijection, not a projection. |
| A2.2 | parameters `factors`, `n` | when the flag holds, `f.base.args` and `f.exp`; when it does not, `f.args` | R | same tuple ↔ `List Factor` bijection as A1/A2. `n` is ignored by the false arm, exactly as the repo ignores an exponent that is not there. |
| A2.3 | result is `factorImage isPowOfAggregate n factors` = `powAll n factors` on the true arm, `factors` on the false arm | `tensor_product_simp_Pow(f).args` vs `f.args` | I | modeled **deeply** (`factorImage` composes the same `powAll`/`powF` as A3); no consumed axiom. Validated mechanically by **G-CONF LANE 2** on the patched tree (mapping.md §3.2). |
| A2.4 | the returned `List Factor` is the factor's image, the commutative part unmentioned | `Mul(*c_part) * tensor_product_simp_Pow(nc_part[0])` — the image scaled by the untouched scalar part | R | the scalar part is carried identically on both sides by G-CONF LANE 2 (`c * …`), so it can neither participate in nor mask the modeled decision (mapping.md §2, last row). |

`Solution_prepatch.lean` reproduces the pre-patch behaviour at **both** sites: at
THE PIN by leaving the factor bare (`result := b :: result`), and at THE ROUTE by
returning `factors` on both arms — i.e. the factor's own positions regardless of
the flag, which is exactly the pre-patch `return e`. It **fails** the added clause
`isPowOfAggregate = true → out = powAll n factors` (G-DIFF).

## B. How the F2P observations distribute over A and A.2 — measured, not argued

`test_tensor_product_simp`'s new assertions do NOT all bottom out in site A:

- `tps(TP(A,B)**x) == TP(A**x, B**x)` — the `Pow` dispatch, site A directly.
- `tps(x*TP(A,B)**2) == x*TP(A**2,B**2)` — a `Mul` with ONE non-commutative
  factor. Pre-patch this never reaches `tensor_product_simp`'s `Pow` branch at
  all: `tensor_product_simp_Mul` returns `e` unchanged at `n_nc == 1`. It is
  resolved by the new `elif n_nc == 1` routing = **site A.2**.
- `tps(x*(TP(A,B)**2)*TP(C,D)) == x*TP(A**2*C,B**2*D)` — a `Mul` whose LEADING
  non-commutative factor is a power. Pre-patch that is the `raise TypeError`
  path. It is resolved by the new leading/trailing-factor routing = **site A.2**,
  after which the pre-existing `TensorProduct`-vs-`TensorProduct` merge (genuinely
  unchanged) combines the positions.
- `tps(TP(A,B) - TP(C,D)**x) == TP(A,B) - TP(C**x,D**x)` — the `Add` branch maps
  `tensor_product_simp` over args, so the changed leg is the bare `Pow` term =
  site A.

**The earlier claim in this section was false, and the correction is measured.** A
previous revision asserted that the `Mul`-branch additions merely *call*
`tensor_product_simp_Pow` and then combine via unchanged machinery, so that
`distributePow` was "the sole carrier of the fix". The combine step is indeed
unchanged; the **routing that gets a power-of-aggregate factor into it is not** —
pre-patch there was no call site to reach. Measured on the official harness:

* base_commit + `tensor_product_simp_Pow` + the `Pow`-branch dispatch ONLY (a
  faithful, complete implementation of site A and nothing else) →
  `FAIL_TO_PASS: test_tensor_product_simp` **fails**, `PASS_TO_PASS` 4/4 pass,
  `resolved: false`.
* base_commit + the same helper + the `tensor_product_simp_Mul` routing edits →
  `resolved: true`.

So site A.2 is an **independently-fixed behavior**: it is not derivable from site
A, and a spec that contracts only site A admits implementations that do not
resolve the task. Both sites are therefore contracted (`distributePow`,
`simplifyFactor`) and both are reproduced in the pre-image by the single
`Solution_prepatch.lean`, which fails an obligation at each site (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The two operations that genuinely *changed* — distributing
the exponent across the factor sequence (A3), and deciding which image one factor
position receives (A2.3) — are both modeled **deeply** (the spelled-out
front-recursive `powAll`; the flag-selected `factorImage` built from it), not
hidden behind an axiom about the functions under change. There is **no consumed
axiom** and **no A-reference** in this bundle: `powF` (the unchanged `**` callee)
is opaque and carries no `ensures`; the proofs consume only the structural unfold
of `powAll`/`factorImage` and the case split on the routing flag. Both deep models
are validated by G-CONF (a mechanical differential test on the patched tree, one
lane each), so no G-AX / `axiom_check.py` is needed or possible (directive 7; both
changed sites are absent or differently shaped at base_commit).

## C.1 Termination semantics: TOTAL correctness

The bundle uses `set_option loom.semantics.termination "total"` (with an
explicit `decreasing i` measure on `distributePow`'s fold loop; `simplifyFactor`'s
impl is loop-free, so its total-correctness obligation is discharged
structurally). Partial-correctness
semantics was a spec-too-weak hole (G-PANEL-1, 2026-08-02): under partial
correctness a same-spec impl whose loop diverges (never reaches the
postcondition) verifies vacuously while returning nothing — admitted by any
partial-correctness contract. The real `tensor_product_simp_Pow` always
terminates (a finite comprehension over `e.base.args` and a constructor call),
and the F2P tests observe its return value, so total correctness is the
faithful semantics; a divergence attack now fails to verify (the decreasing
obligation is unprovable for a non-terminating loop) while the position-wise
raise still verifies.

## D. verify(Solution) ⇒ resolved

The claim now rests on TWO obligations, one per changed site, and needs both.

1. **THE PIN.** `distributePow` verifies only if its output equals the exact
   position-wise raise `powAll n factors` (A3) — same arity, same order, every
   factor raised. By R (`tuple ↔ List Factor`, exponent ↔ `n`, aggregate
   reconstruction) the verified result equals
   `TensorProduct(*[ b**e.exp for b in e.base.args])`; by G-CONF LANE 1 that R/I
   transliteration agrees with `patch.diff`'s public behavior
   (`tensor_product_simp` over `Pow` nodes) on ≥10⁵ inputs.
2. **THE ROUTE.** `simplifyFactor` verifies only if its output is
   `factorImage isPowOfAggregate n factors` — and its two conditional clauses pin
   each arm separately: `isPowOfAggregate = true → out = powAll n factors` forbids
   handing a power-of-aggregate factor back untouched (the pre-patch `return e`),
   and `isPowOfAggregate = false → out = factors` forbids raising a factor that
   carries no exponent. By R (A2.1–A2.4) the verified result equals
   `tensor_product_simp_Pow(f).args` respectively `f.args`; by G-CONF LANE 2 that
   R/I transliteration agrees with the patched `tensor_product_simp` on product
   nodes over ≥10⁵ inputs with **both arms required to have been reached**.

Together the two obligations cover every F2P assertion (§B maps each assertion to
one of the two sites), so a model satisfying this spec, refined by the maps above,
is the gold patch up to type refinement at both changed sites — and the gold patch
resolves (G-RESOLVE). That neither obligation alone suffices is the measurement in
§B: site A implemented perfectly and site A.2 left at its pre-patch behaviour is
`resolved: false`. The single trust point is refinement fidelity (this doc +
G-CONF's two lanes); there is no consumed-axiom trust point and no G-AX trust
point.
