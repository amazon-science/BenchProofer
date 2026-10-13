# refinement.md — sympy__sympy-18189

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`reorderSolutions` `do` block, the `reorderAll`/`reorderTuple` pure model, and the
`baseSolve` opaque callee) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized/opaque callee — **A-consumed** where
the proof uses an asserted `ensures`, **A-reference** where an opaque/deep model
is validated against the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reorder branch — `diophantine` (`sympy/solvers/diophantine.py:182-185`)

Gold hunk:
```
  if syms != var:
      dict_sym_index = dict(zip(syms, range(len(syms))))
      return {tuple([t[dict_sym_index[i]] for i in var])
-                 for t in diophantine(eq, param)}
+                 for t in diophantine(eq, param, permute=permute)}
```

| # | Solution.lean impl op (`reorderSolutions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `order : List Nat` | the positional permutation `[dict_sym_index[i] for i in var]` derived from `syms`/`var` | R | the Python permutation list ↔ `order : List Nat` (mapping.md §2). Upstream `dict(zip(syms, range))` machinery is unchanged input; only its resulting permutation is observed. |
| A2 | parameter `permute : Bool` | the `permute` keyword of `diophantine` | R | `Bool` ↔ Python bool, identity (mapping.md §2). |
| A3 | `let base := baseSolve permute` | `diophantine(eq, param, permute=permute)` (the recursive `syms=None` solve) | **A-reference** | the base solver is the UNCHANGED callee invoked with the caller's flag; modeled opaque (no `ensures`), validated == the real recursive `diophantine(eq, param, permute=p)` by G-AX (mapping.md §3.1). **The forwarded `permute` is the entire content of the fix** — pre-patch this op received the default `False`. |
| A4 | `let result := reorderAll order base` | `{tuple([t[dict_sym_index[i]] for i in var]) for t in <base>}` | I | the per-tuple positional gather + set-build, transliterated concretely. `reorderTuple order t = order.map (t[·]!)` ⇔ `tuple([t[dict_sym_index[i]] for i in var])`; `reorderAll` maps it over the set. G-CONF transliterates this R/I leg. |
| A5 | `return result` (`List (List Int)`) | `return {…}` (the Python `set`) | R | the result `set` ↔ `List (List Int)` compared as a set (mapping.md §2); `test_diophantine` compares set membership. |

Discriminating content of the change — the variant flag reaching the base solver
— lives in A3: `baseSolve permute` (model) ⇔ `diophantine(eq, param,
permute=permute)` (real). Pre-patch the recursive call omitted `permute`, so it
ran with `permute=False`; `Solution_prepatch.lean` reproduces that with
`baseSolve false` and **fails** the clause
`out = reorderAll order (baseSolve permute)` (G-DIFF): the unsolved goal is
exactly `reorderAll order (baseSolve false) = reorderAll order (baseSolve permute)`,
which fails when `permute = true` and the base solver's `true`-set differs from
its `false`-set (the issue's `m**4 + n**4 - 97`: 8 vs 1 solutions).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — forwarding
the `permute` flag into the recursive base solve — is captured at the type level
(A2/A3: the flag is a `Bool` argument threaded to the opaque callee, exactly as
the patch threads it), not hidden behind an over-claiming axiom. The base solver
is modeled **opaque** (the weakest possible contract: no `ensures`), so the spec
borrows nothing from it except its functional dependence on `permute` — which is
the very thing the patch corrects. There is no consumed axiom; the only A content
is the A-reference `baseSolve`, validated against the real callee by G-AX.

## C. verify(Solution) ⇒ resolved

`reorderSolutions` verifies only if its output equals
`reorderAll order (baseSolve permute)` — i.e. the reindexing applied to the base
set the solver produces **for the requested flag** (A3 + A4). By R (`set ↔ List
(List Int)` as a set, the permutation ↔ `order`, the `Bool` identity) the verified
result equals `{tuple([t[dict_sym_index[i]] for i in var]) for t in
diophantine(eq, param, permute=permute)}` on the tested inputs; by G-AX the opaque
`baseSolve` is the real recursive `diophantine` per flag (A-reference) and the
flag is load-bearing; by G-CONF the R/I transliteration of the reindexing applied
to the real `permute`-forwarded base solve agrees with the gold-patched
`diophantine(eq, syms, permute)` on ≥10⁵ inputs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). Trust points are exactly
the two of plan §1.1: opaque-callee soundness (G-AX) and refinement fidelity (this
doc, G-EQ + G-CONF).
