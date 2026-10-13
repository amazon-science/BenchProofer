# refinement.md — sympy__sympy-21379

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`extractCommonFactor` `do` block plus the pure deep model `extractSpec`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(a deep model validated == the real callee by G-AX), or **I** (identical concrete
op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — the shared-factor-extraction block of `Mod.eval`

Repo construct: `sympy/core/mod.py`, classmethod `Mod.eval`, the block
`# extract gcd …` through `pwas, qwas = p, q` (`mod.py:168-173` @ base_commit).

Gold hunk (the behavioral change; the new import at `mod.py:43` is support):
```
-        G = gcd(p, q)
-        if G != 1:
-            p, q = [
-                gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]
+        try:
+            G = gcd(p, q)
+            if G != 1:
+                p, q = [gcd_terms(i/G, clear=False, fraction=False)
+                        for i in (p, q)]
+        except PolynomialError:  # issue 21373
+            G = S.One
         pwas, qwas = p, q
```

| # | Solution.lean impl op (`extractCommonFactor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `p q : Int` | `p`, `q` (sympy `Expr` operands in scope at the block) | R | `Expr` ↔ `Int` opaque handle (mapping.md §2); only equality / the distinguished factor `1` is observed, never arithmetic. G-CONF bridges by running the real block on real `Expr` pairs. |
| A2 | `match commonFactor p q with …` (branch on the success/raise OUTCOME of the shared-factor computation) | `try: G = gcd(p, q) … except PolynomialError:` | A-reference + I | the unchanged callee `gcd` is modeled `opaque` with NO `ensures`; the `Except`-leg reification of "returns / raises `PolynomialError`" is the **A-reference** G-AX validates against the real `gcd` (mapping.md §3.1). The `match` that dispatches on that outcome — i.e. the `try/except` control flow itself — is **I** (transliterated 1:1 by G-CONF). |
| A3 | `Except.error _ => (1, p, q)` (recover: trivial factor `1`, both operands unchanged) | `except PolynomialError: G = S.One` (with `p, q` never reassigned inside the `try` before the raise) | I | identical control flow: on the raise, the factor becomes the trivial factor `1` and the operands keep their pre-block values. This is the discriminating clause the bug violates (pre-patch propagates the raise). `1 : Int` ↔ `S.One` (mapping.md §2). |
| A4 | `Except.ok g => if g = 1 then (g, p, q)` (trivial factor ⇒ no reduction) | `if G != 1:` taken false ⇒ `p, q` unchanged | I | the `G != 1` guard's false branch; operands unchanged. |
| A5 | `else (g, reduceTerm p g, reduceTerm q g)` (non-trivial factor ⇒ reduce each operand by the factor) | `p, q = [gcd_terms(i/G, clear=False, fraction=False) for i in (p, q)]` | A-reference + I | the unchanged callee `gcd_terms` is `opaque` with NO `ensures` (mapping.md §3.2); its presence keeps the success path skeleton-faithful. The list-comprehension over `(p, q)` is the **I** per-operand map; G-CONF runs the real `gcd_terms`. Reached only when the factor is non-trivial — the path the change does not alter. |
| A6 | `return Except.ok result` (the step never itself fails — every outcome yields a triple) | the block falls through to `pwas, qwas = p, q`; `Mod.eval` continues, no exception leaves the block | I | totality of the recovered block: control always reaches the next statement with a well-defined `(G, p, q)`. The `Except.ok` wrapper records "no failure escapes"; the pre-patch's escaping `Except.error` is exactly the defect. |

Discriminating content of the change — a raised shared-factor failure must be
RECOVERED (factor `1`, operands unchanged) rather than PROPAGATED — lives in the
`Except.error _ => (1, p, q)` leg (A3) ⇔ the new `except PolynomialError: G =
S.One`. `Solution_prepatch.lean` reproduces the unguarded pre-patch behavior
(`Except.error e => Except.error e`, propagating the failure) and **fails**
`out = Except.ok (extractSpec p q)` precisely on that leg (G-DIFF; confirmed: the
prepatch's unsolved goal is the `Except.error` case where `Except.error e ≠
Except.ok (1, p, q)`).

## B. No consumed axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The two callees `gcd` (`commonFactor`) and `gcd_terms`
(`reduceTerm`) are **unchanged** by this change — the patch wraps the call site in
a `try/except`, it does not redefine them. They are modeled `opaque` with **NO
asserted `ensures`**, so there is **no consumed axiom** to over-claim (directive
7): the desired behavior assumes nothing about WHICH factor `gcd` returns, only
how a success vs a raise is handled. They are tagged **A-reference** — G-AX
validates the modeled facts about them against the real callees (mapping.md §3):
the `Except.error` leg is real and reachable, the raised exception is exactly
`PolynomialError`, and the `Except.ok` leg is real on polynomial operands.

The operation that genuinely *changed* — adding the recovery on a raised
shared-factor failure — is the `match`/recover control flow, modeled **directly**
(A2/A3, an I leg over an A-reference callee), not hidden behind an axiom about the
function under change. There is no axiom about `Mod.eval` itself.

## C. verify(Solution) ⇒ resolved

`extractCommonFactor` verifies only if its output equals `extractSpec p q` for
every outcome of the opaque `commonFactor` — including the `Except.error` leg,
which forces the recovery `(1, p, q)` (A3). By R (`Expr ↔ Int` handle, `S.One ↔
1`) and the I transliteration of the `try/except` / guard / per-operand map, the
verified block equals the gold patch's recovered block on the tested operand
pairs; by G-AX the real `gcd` raises exactly `PolynomialError` on the issue's
`Piecewise`-bearing operand (so the recovery branch is the genuine runtime path)
and succeeds on polynomial operands; by G-CONF the R/I shadow of the block agrees
with `patch.diff`'s behaviour on ≥10⁵ fuzzed `(p, q)` pairs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: callee-fact soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
