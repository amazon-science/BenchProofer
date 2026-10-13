# mapping.md — sympy__sympy-21379

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 624217179aaf8d094e6ff75b7493ad1ee47599b0`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `sympy/core/mod.py` (the classmethod `Mod.eval`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `extractCommonFactor (p : Int) (q : Int)` | the common-factor-extraction step of `Mod.eval` — `sympy/core/mod.py:168-173` (the block `# extract gcd …` through `pwas, qwas = p, q`) | the modeled changed code region |
| `commonFactor` *(opaque — UNCHANGED callee)* | `gcd(p, q)` — `sympy/polys/polytools.py:5281` (imported into `Mod.eval` at `mod.py:43`) | the common-factor routine the region calls; it may raise on operands whose generators are not polynomial (e.g. a `Piecewise`) |
| `reduceTerm` *(opaque — UNCHANGED callee)* | `gcd_terms(i/G, clear=False, fraction=False)` — `sympy/core/exprtools.py` (imported at `mod.py:42`), applied to each of `p, q` | the per-operand simplification applied only when a non-trivial common factor was found |
| `PolyErr.polynomialError` | `PolynomialError` — `sympy/polys/polyerrors.py:115`; raised at `sympy/polys/polytools.py:4399` (`"… generators do not make sense"`) | the recoverable failure shape of the common-factor routine |
| `extractSpec` *(pure spec; the deep model of the region's intended behavior)* | the post-patch block `mod.py:168-176` (the `try/except` and its body) | pure spec: the operands-and-factor triple the region must produce |

The pre-patch repo construct the change fixes (refinement audit only): the
unguarded `G = gcd(p, q); if G != 1: …` at `mod.py:169-172`, which lets the
common-factor routine's failure propagate out of `Mod.eval`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a symbolic expression operand (`p`, `q`: sympy `Expr`) | `Int` (opaque handle) | each distinct `Expr` value ↔ a distinct `Int` handle; only object identity / equality is observed, never arithmetic. The carrier `Int` is an abstract handle domain, NOT a model of the expression's numeric value. |
| the common factor `G` (a sympy `Expr`) | `Int` (opaque handle) | likewise a handle; the only distinguished handle value is the trivial factor `1` (sympy `S.One`), which the region's guard `G != 1` and the recovery `G = S.One` both name. `1 : Int` ↔ `S.One`. |
| `gcd(p, q)` returning an `Expr` | `commonFactor p q = Except.ok g` | a successful common-factor computation yields a factor handle |
| `gcd(p, q)` raising `PolynomialError` | `commonFactor p q = Except.error .polynomialError` | the raise is reified as the error leg of an `Except`; the `try/except PolynomialError` is reified as a `match` on that `Except` |
| `gcd_terms(i/G, …)` over `i ∈ (p, q)` | `reduceTerm i g` | the per-operand simplification, an opaque map from an operand handle and the factor handle to the simplified operand handle |
| the `(G, p, q)` triple after the block | `Int × Int × Int` | `(factor, firstOperand, secondOperand)`; tuple ↔ tuple component-wise |

`Int` is used purely as an abstract, decidable-equality handle domain — the
behavior under specification is control-flow over an opaque callee's
success/raise outcome, not numeric computation, so no numeric carrier (`Real`,
`Rat`) is warranted. The only handle whose identity matters is the trivial
factor `1`.

## 3. Callee provenance (G-AX)

### 3.1 `commonFactor` ↔ `gcd` (opaque, UNCHANGED callee — no consumed contract)
**Callee:** `sympy.polys.polytools.gcd`, imported into `Mod.eval` at `mod.py:43`
and called at `mod.py:169`. It is **unchanged** by this change — the change
wraps the call in a `try/except`, it does not redefine `gcd`. Modeled as the
`opaque` free function `commonFactor : Int → Int → Except PolyErr Int`. **No
`ensures` is asserted about it**, so there is no contract to validate point-wise
against the callee (no consumed axiom; G-AX does not check an `ensures` here).

What G-AX (`axiom_check.py`) DOES establish — the real-world facts that make the
modeled control flow non-vacuous and faithful:
  1. **The error leg is real and reachable:** the real `gcd` actually raises
     `PolynomialError` on the operands the issue exhibits (the `Piecewise`-bearing
     argument of `Mod`), so the modeled `Except.error` branch corresponds to a
     genuine runtime outcome — the recovery branch is not dead code.
  2. **The raised exception is exactly `PolynomialError`** (a `BasePolynomialError`
     subclass, `polyerrors.py:115`), matching the single exception type the
     `except` clause catches — not a broader/narrower class.
  3. **The recovery is correct end-to-end:** with the gold patch applied,
     evaluating the issue's `expr.subs({1: 1.0})` (which routes through
     `Mod.eval`) no longer raises and returns a value; pre-patch it raises
     `PolynomialError`. This pins that catching the error and recovering with the
     trivial factor `G = S.One` (and leaving `p, q` unchanged) is the resolving
     behavior.

### 3.2 `reduceTerm` ↔ `gcd_terms` (opaque, UNCHANGED callee)
**Callee:** `sympy.core.exprtools.gcd_terms`, imported at `mod.py:42`, applied at
`mod.py:172` to `i/G` for each `i ∈ (p, q)`. Reached **only** when the
common-factor computation succeeded with a non-trivial factor (`G != 1`) — i.e.
on the success path, which the change does not alter. Modeled as `opaque
reduceTerm : Int → Int → Int`; no `ensures` asserted, nothing to validate
point-wise. Its presence in the spec keeps the success path skeleton-faithful
(the change leaves that path's body identical inside the new `try`).

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`21379`**. See that file
and §3 of refinement.md for why the differential test reduces to the
success/raise dichotomy of the unchanged callee `gcd` (the only computational
content the impl region adds over the callees is the `match` on that outcome).
