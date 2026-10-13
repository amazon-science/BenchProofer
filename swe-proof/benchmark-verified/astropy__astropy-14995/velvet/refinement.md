# refinement.md — astropy__astropy-14995

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `resolveMask` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == a real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (here, zero) A legs and this narrative are audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The mask-resolution site — `_arithmetic_mask` (`ndarithmetic.py:485`)

Gold hunk (the behaviour-relevant line; a same-hunk comment typo fix is inert):
```
-        elif operand is None:
+        elif operand.mask is None:
             return deepcopy(self.mask)
```

| # | Solution.lean impl op (`resolveMask`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `selfMask`, `operandMask : Option (List Int)` | `self.mask`, `operand.mask` | R | a mask is `None` or an integer array ↔ `none` / `some <elements>` (mapping.md §2). G-CONF bridges via `Option ↔ (None\|ndarray)`. |
| A2 | param `handleMaskNone : Bool` | `handle_mask is None` | R | boolean flag ↔ `Bool` (mapping.md §2). |
| A3 | param `operandPresent : Bool`, `require operandPresent = true` | `operand is not None` (always true on the binary-op path that reaches this function) | R | the spec's domain (mapping.md §2/§3): `_arithmetic_mask` is only reached with a wrapped, real second operand. |
| A4 | param `combine : List Int → List Int → List Int` | `handle_mask` callable | R | caller-supplied combiner ↔ function parameter (mapping.md §3). Applied only in the both-present arm. |
| A5 | `if (selfMask = none ∧ operandMask = none) ∨ handleMaskNone = true then none` | `if (self.mask is None and operand is not None and operand.mask is None) or handle_mask is None: return None` | I | identical guard under R. (`operand is not None` is the spec domain A3, so the conjunct is `True` and drops out — same condition.) |
| A6 | `else if selfMask = none then operandMask` | `elif self.mask is None and operand is not None: return deepcopy(operand.mask)` | I + R | first-mask-absent ⇒ carry the second operand's mask over. `deepcopy` is identity on content (mapping.md §2, the R). `operand is not None` again drops out by A3. |
| A7 | `else if operandMask = none then selfMask` | `elif operand.mask is None: return deepcopy(self.mask)` | I + R | **the fixed branch**: second-mask-absent ⇒ carry the FIRST operand's mask over. `deepcopy` = identity (R). |
| A8 | `else some (combine (selfMask.getD []) (operandMask.getD []))` | `else: return handle_mask(self.mask, operand.mask, **kwds)` | I | both present ⇒ apply the combiner to the two present mask values. `combine`/`handle_mask` is the same callable fed to both legs by G-CONF (mapping.md §3). |

Discriminating content of the change — when the FIRST operand has a mask and the
SECOND operand's mask is absent (`selfMask ≠ none ∧ operandMask = none`), the
result must be `selfMask` (A7), NOT a combiner call against an absent mask. The
pre-patch guarded this branch on `operand is None` (`operandPresent = false`),
which is never true for a real binary operand, so the masked×no-mask case fell
through to A8 (the combiner) — exactly the issue's
`TypeError: unsupported operand type(s) for |: 'int' and 'NoneType'`.
`Solution_prepatch.lean` reproduces that guard and **fails** the postcondition
`(handleMaskNone = false ∧ selfMask ≠ none ∧ operandMask = none) → out = selfMask`
(G-DIFF) — confirmed: the unsolved goal is exactly that clause.

## B. No A-tagged steps; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There are **no consumed axioms** and **no A-reference deep
models**: the changed operation is a finite case split fully expressible in
Velvet, and the only callable it delegates to (`handle_mask`) is a parameter of
the function under spec, modeled directly as `combine` (A4/A8), not an
axiomatized library callee. No `axiom_check.py` is shipped; G-AX skips.

The single in-hunk comment change (`# Now lets …` → `# Now let's …`) is a typo
fix with no behavioural content — not represented as an op (no leakage either:
it is not in the spec view).

## C. verify(Solution) ⇒ resolved

`resolveMask` verifies only if `out` equals, in every case, the mask demanded by
the case split: `none` when handling is declined or neither mask is present
(A5); the present mask carried over in each single-mask case (A6, A7 — A7 is the
fix); and the combiner applied to both present masks (A8). By R (`Option ↔
None/array`, `deepcopy`/`mark`-free identities, `handle_mask ↔ combine`) the
verified routine equals the patched `_arithmetic_mask` on the tested inputs; by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed inputs across the issue's five scenarios and four combiners. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). There are no axiom
trust points (no A legs); the sole trust point is refinement fidelity (this doc,
G-EQ + G-CONF).
