# refinement.md — matplotlib__matplotlib-24870

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`chooseLevelArg` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the overall correspondence narrative is audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The selection site — `_process_contour_level_args` (`contour.py:1119`)

Gold hunk (the changed `levels_arg` selection):
```
 if self.levels is None:
-    if len(args) == 0:
-        levels_arg = 7  # Default, hard-wired.
-    else:
+    if args:
         levels_arg = args[0]
+    elif np.issubdtype(z_dtype, bool):
+        if self.filled:
+            levels_arg = [0, .5, 1]
+        else:
+            levels_arg = [.5]
+    else:
+        levels_arg = 7  # Default, hard-wired.
 else:
     levels_arg = self.levels
```

| # | Solution.lean impl op (`chooseLevelArg`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `if levelsKwSet then return levelsKw` | `if self.levels is None: … else: levels_arg = self.levels` | R + I | the `self.levels is not None` guard ↔ `levelsKwSet = true`; selecting `self.levels` ↔ returning `levelsKw`. Boolean/value refinement (mapping.md §3). |
| A2 | `else if posGiven then return posArg` | `if args: levels_arg = args[0]` | R + I | `bool(args)` ↔ `posGiven`; `args[0]` ↔ `posArg`. The gold's `if args:` truthiness on a list is exactly "non-empty" (mapping.md §3). |
| A3 | `else if boolField then (if filled then explicit [0,1/2,1] else explicit [1/2])` | `elif np.issubdtype(z_dtype, bool): if self.filled: levels_arg = [0, .5, 1] else: levels_arg = [.5]` | R + I | `np.issubdtype(z_dtype, bool)` ↔ `boolField`; `self.filled` ↔ `filled`; the two literal lists ↔ `explicit [0,1/2,1]` / `explicit [1/2]` (`0,.5,1` exact in `Rat` and IEEE-754, mapping.md §3). **The behavioural change the F2P test pins.** |
| A4 | `else return (count 7)` | `else: levels_arg = 7  # Default, hard-wired.` | R + I | the hard-wired default count `7` ↔ `count 7` (mapping.md §3). |

Control-flow note: Python `if/elif/elif/else` is transliterated as nested
`if … else (if …)` because Velvet has no `else if` (plan §3). The nesting is
order-faithful: keyword-set > positional > boolean-field > default, identical to
the gold's branch order.

## B. The supporting dtype-plumbing — `_contour_args` / `_check_xyz` / tri `_contour_args` (R)

Gold also: (i) gives `_process_contour_level_args` a new `z_dtype` parameter and
passes `z.dtype`; (ii) drops the `dtype=np.float64` coercion on `z`
(`ma.asarray(z)` instead of `ma.asarray(args[0], dtype=np.float64)`, and the
analogous change in `_check_xyz` and the tri variant). These are **R
(type-plumbing)**: they carry the *un-coerced* dtype to the selection site so
`boolField` (= `np.issubdtype(z.dtype, bool)`) is true exactly when the user
passed a boolean field. They do not alter the selection logic of A1–A4; they
establish the binding of `chooseLevelArg`'s `boolField` parameter (mapping.md
§2). No separate modeled method or prepatch is needed — the dtype plumbing has no
observable effect except via `boolField`, which §A already discriminates: a patch
that keeps the `float64` coercion makes `boolField` permanently false, so its
behaviour equals the prepatch's (`count 7` always) and fails the F2P test. Its
correctness is carried by G-RESOLVE (`patch.diff` == gold) + G-CONF (the oracle
runs the real patched plumbing).

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I; there is no A leg (no axiom, no deep-model reference). The
operation that genuinely *changed* — adding the boolean-field branch and its two
fixed level specifications — is modeled **directly** in the `do` block (A3), not
hidden behind an axiom. `np.issubdtype(z.dtype, bool)` and `self.filled` are
inputs the routine has already computed, not callees of the modeled function, so
nothing about them is axiomatized. G-AX is therefore vacuous (recorded as such in
meta.json); the impl region is all-R/I, so G-CONF runs (not skipped).

## D. verify(Solution) ⇒ resolved

`chooseLevelArg` verifies only if it selects the explicit boundary specification
for a boolean field — `[.5]` when not filled, `[0, .5, 1]` when filled (A3) — and
otherwise reproduces the prior precedence (keyword > positional > default count
`7`). By R (the Boolean/`int`/`list` ↔ `Bool`/`count`/`explicit` bijections,
mapping.md §3) the verified selection equals the gold patch's `levels_arg`
computation on every flag combination; by §B the `boolField` input faithfully
tracks the un-coerced dtype. The downstream processing
(`isinstance(levels_arg, Integral)` → `_autolev`/`np.asarray`, level filtering)
is unchanged by the patch and identical for both branches, so equal `levels_arg`
⇒ equal `self.levels`. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no trust points beyond the type bijection (no axiom):
G-CONF mechanically refutes the R/I legs over the full flag cube.
